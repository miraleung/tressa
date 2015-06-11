/**
 * Tressa.cpp
 * 2015/06/02
 *
 * Instruments code to execute asserts at predefined points (in a separate .cpp file).
 *
 */


#define DEBUG_TYPE "tressa"
#include <cxxabi.h>
#include <map>
#include <string>

#include "llvm/Function.h"
#include "llvm/Instructions.h"
#include "llvm/Instruction.h"
#include "llvm/Pass.h"
#include "llvm/LLVMContext.h"
#include "llvm/Module.h"
#include "llvm/Type.h"
#include "llvm/Value.h"

#include "llvm/ADT/StringRef.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Support/InstIterator.h"
#include "llvm/Support/IRBuilder.h"

using namespace llvm;

/** =====================
 *  TRESSA FOR C
 *  ===================== */

namespace {
  struct TressaInsert : public ModulePass {
    static char ID;
    Function *hook_assert_fn;
    TressaInsert() : ModulePass(ID) { }

    enum InsertStm {
      kUndefn = -1,
      kIf = 0,
      kFor,
      kStm,
      kCall,
      kReturn
    };

    virtual bool runOnModule(Module &M) {
      Constant *hookFunc;

      // Vector of global values;
      std::vector<GlobalVariable*> globals_vt;
      // Vector of assert fns to run (insert) for fns
      std::vector<Function*> fnvector;
      // Vector of names of targeted (insert-ee) fns
      std::vector<std::string> fn_vt;
      std::map<std::string, std::map<std::string, Value*> > assertfn_args_map_map;

      // Vectors for insertion location and stm type.
      std::vector<std::vector<InsertStm> > insertStm_vt_vt;
      std::vector<std::vector<int> > insertIthStm_vt_vt;
      std::vector<std::vector<std::string> > callInstFn_vt_vt;
      // <K, V> = <assertfn name, variables' names' vector>
      std::map<std::string, std::vector<std::string> > assertfn_varnames_map;

      // Strings
      // Asserts for class-less functions
      // TODO: FIX
      std::string assert_fn_prefix = "assertfn_";

      // Information-gathering iteration.
      // Find the names of targeted (insert-ee) functions.
      for (Module::iterator assertFun = M.begin(), assertFunE = M.end();
          assertFun != assertFunE; ++assertFun) {
        std::string assertFun_name = assertFun->getNameStr();
        // Function asserts
        if (assertFun_name.compare(0,
                assert_fn_prefix.size(), assert_fn_prefix)) {
          continue;
        }

        Function::ArgumentListType &argList = assertFun->getArgumentList();

        // Must have at least one arg
        if (!argList.size()) {
          continue;
        }

        std::string targeted_fn_name = argList.front().getNameStr();

        fn_vt.push_back(targeted_fn_name);

        std::map<std::string, Value*> assertfn_args_map;
        // TODO: HANDLE CASE WHEN FIRST TYPE IS NOT INT OR DENOTES INVALID FUNCTION NAME
        // Build assert (hook) function.
        std::vector<Type*> params_vt;
        for (Function::arg_iterator arg_iter = assertFun->arg_begin();
            arg_iter != assertFun->arg_end(); ++arg_iter) {
          params_vt.push_back(arg_iter->getType());
          assertfn_args_map.insert(
              std::pair<std::string, Value*>(arg_iter->getNameStr(), arg_iter));
        }
        assertfn_args_map_map.insert(
            std::pair<std::string, std::map<std::string, Value*> >(
              assertFun_name, assertfn_args_map));
        ArrayRef<Type*> *args_ra = new ArrayRef<Type*>(params_vt);
        FunctionType *hookFuncTy = FunctionType::get(assertFun->getReturnType(),
            *args_ra, assertFun->isVarArg());
        hookFunc = M.getOrInsertFunction(assertFun->getName(), hookFuncTy);
        hook_assert_fn = cast<Function>(hookFunc);
        fnvector.push_back(hook_assert_fn);

        // Get variables in assert fn
        // API req: have same name as targeted fn's assert vars.
        Function *targetedFun = M.getFunction(StringRef(targeted_fn_name));
        std::vector<std::string> local_var_names_vt;
        std::vector<AllocaInst*> assertfn_alloca_vt;

        std::vector<std::string> targeted_fn_local_var_names_vt;
        std::vector<Value*> targeted_fn_values_vt;

        std::string keyword_insert_locn_var = "_" + assert_fn_prefix;
        std::string keyword_call = "call";
        std::string keyword_if = "if";
        std::string keyword_for = "for";
        std::string keyword_return = "return";
        std::vector<InsertStm> insertStm_vt;
        std::vector<int> insertIthStm_vt;
        std::vector<std::string> callInstFn_vt;

        // Locals' vector (loads only, no storeinst)
        std::vector<std::string> varnames_vt;

        InsertStm insertStmType = kUndefn;
        int insertIthStm = -1;
        std::string callInstFnName = "";

        // Get names of local variables in assert fns.
        for (Function::iterator BB = assertFun->begin(),
            BBE = assertFun->end(); BB != BBE; ++BB) {
          // ASSUMPTION: Only one insertion point
          // TODO: FAIL if no insertion point found
          for (BasicBlock::iterator BI = BB->begin(), BIE = BB->end();
              BI != BIE; ++BI) {
            if (isa<AllocaInst>(&(*BI))) {
              AllocaInst *allocaInst = dyn_cast<AllocaInst>(BI);
              std::string local_var_name = allocaInst->getNameStr();
              // Interested only in denotation of insertion point.
              if (local_var_name.find(keyword_insert_locn_var) >= std::string::npos) {
                continue;
              }

              // Denotes location in targeted fn to insert this assertfn.
              // Return and call stms: Pre. All else: post
              if (local_var_name.find(keyword_insert_locn_var) < std::string::npos) {
                int ith_stridx = keyword_insert_locn_var.length();
                if (local_var_name.find(keyword_if) < std::string::npos) {
                  insertStmType = kIf;
                  ith_stridx += keyword_if.length();
                } else if (local_var_name.find(keyword_for) < std::string::npos) {
                  insertStmType = kFor;
                  ith_stridx += keyword_for.length();
                } else if (local_var_name.find(keyword_call) < std::string::npos) {
                  insertStmType = kCall;
                  ith_stridx += keyword_call.length();
                  // TODO: Specify ith call
                  insertIthStm = 0;
                } else if (local_var_name.find(keyword_return) < std::string::npos) {
                  insertStmType = kReturn;
                  insertIthStm = 0;
                } else {
                  continue;
                }

                // TODO: Check last char is int, else throw error
                int var_name_idx = local_var_name.find_last_of("_");
                if (insertStmType != kReturn && insertStmType != kCall
                    && var_name_idx >= ith_stridx) {
                  insertIthStm = atoi(local_var_name.substr(var_name_idx+1).c_str());
                }
                // ASSUMPTION: If no fn name specified, no insertion is done.
                if (insertStmType == kCall && var_name_idx >= ith_stridx) {
                  callInstFnName = local_var_name.substr(var_name_idx+1);
                }
                insertStm_vt.push_back(insertStmType);
                insertIthStm_vt.push_back(insertIthStm);
                callInstFn_vt.push_back(callInstFnName);
              }
            }
          }
        }
        // TODO: Specify assert fn and targeted fn name in fail msg.
        // TODO: May need an assert macro.
        /* */ errs() << "Doing " << hook_assert_fn->getNameStr() << "\n";
        assert(insertStmType != kUndefn && insertIthStm >= 0
            && "Insertion point of assert function "
            && " not defined.");

        insertStm_vt_vt.push_back(insertStm_vt);
        insertIthStm_vt_vt.push_back(insertIthStm_vt);
        callInstFn_vt_vt.push_back(callInstFn_vt);
      }


      // Code instrumentation iteration.
      // Iterates over all the targeted functions.
      int fnvector_idx = 0;
      for (std::vector<std::string>::iterator VI = fn_vt.begin(),
          VE = fn_vt.end(); VI != VE; ++VI, fnvector_idx++) {
        // Targeted function
        Function *F = M.getFunction(StringRef(*VI));
        // Build a map of <varnames, pointer operands>
        std::map<std::string, Value*> varname_ptr_map;

        // TODO: ABORT IS F IS NULL OR SOMETHING
        std::vector<InsertStm> insStm_vt = insertStm_vt_vt.at(fnvector_idx);
        std::vector<int> ith_stm_idx_vt = insertIthStm_vt_vt.at(fnvector_idx);
        std::vector<std::string> callFnName_vt = callInstFn_vt_vt.at(fnvector_idx);
        std::string assertfn_name = fnvector.at(fnvector_idx)->getNameStr();

        for (int vt_idx = 0; vt_idx < (int) insStm_vt.size(); vt_idx++) {
          int curr_stm_idx = 0;
          InsertStm insStm = insStm_vt.at(vt_idx);
          int ith_stm_idx = ith_stm_idx_vt.at(vt_idx);
          std::string callFnName = callFnName_vt.at(vt_idx);
          // TODO: ABORT IF ARGS NOT FOUND
          std::map<std::string, std::map<std::string, Value*> >::iterator
            assertfn_args_map_map_iter = assertfn_args_map_map.find(assertfn_name);
          errs() << "\tASSERTFN_NAME: " << assertfn_name << "\n";
          if (assertfn_args_map_map_iter == assertfn_args_map_map.end()) {
            // TODO: BETTER ERROR MESSAGE
            errs() << "\tDid not find map for " << assertfn_name << "\n";
            continue;
          }
          errs() << "\tFound map for " << assertfn_name << "\n";
          std::map<std::string, Value*> assertfn_args_map = assertfn_args_map_map_iter->second;

          // Iterate over argument list
          std::vector<std::string> argnames_vt;

          for (Function::arg_iterator arg_iter = F->arg_begin();
              arg_iter != F->arg_end(); ++arg_iter) {
            argnames_vt.push_back(arg_iter->getNameStr());
          }


          // TODO: Remove
          std::map<std::string, Value*> targeted_fn_varname_value_map;

          /* errs() << "\t\tinsStm is " << insStm << "; idx = " << ith_stm_idx << "\n"; */
          for (Function::iterator BB = F->begin(), E = F->end(); BB != E; ++BB) {
            std::string bbLabel = (*BB).getNameStr();

            // Find pointer operands
            for (BasicBlock::iterator BI = BB->begin(), BIE = BB->end();
                BI != BIE; ++BI) {
              // AllocaInst: Get pointer operands
              if (isa<AllocaInst>(&(*BI))) {
                // Instruction is pointer itself.
                AllocaInst *allocaInst = dyn_cast<AllocaInst>(BI);
                std::string ptr_name = allocaInst->getNameStr();
                // Valid only if this is a function arg
                size_t addr_str_idx = ptr_name.find(".addr");
                if (addr_str_idx < std::string::npos) {
                  ptr_name = ptr_name.substr(0, addr_str_idx);
                  errs() << "\targname is " << ptr_name;
                  std::vector<std::string>::iterator argnames_iter =
                    std::find(argnames_vt.begin(), argnames_vt.end(), ptr_name);
                  if (argnames_iter == argnames_vt.end()) {
                    continue;
                  }
                }
                std::map<std::string, Value*>::iterator assertfn_args_map_iter =
                  assertfn_args_map.find(ptr_name);
                if (assertfn_args_map_iter == assertfn_args_map.end()) {
                  errs() << "\tCould not find " << ptr_name << "\n";
                  continue;
                }
                errs() << "\tvarname inserting " << ptr_name << "\n";
                varname_ptr_map.insert(
                    std::pair<std::string, Value*>(ptr_name, allocaInst));

              }
            }

            if (insStm == kReturn
                || insStm == kCall
                || (curr_stm_idx == ith_stm_idx
                  && ((insStm == kIf
                      && bbLabel.find("if.end") < std::string::npos)
                    || (insStm == kFor
                      && bbLabel.find("for.end") < std::string::npos)))) {

              TressaInsert::runOnBasicBlockForFn(BB, fnvector.at(fnvector_idx), insStm,
                  varname_ptr_map,
                  callFnName);
            }

            if ((insStm == kIf && bbLabel.find("if.end") < std::string::npos)
                || (insStm == kFor && bbLabel.find("for.end") < std::string::npos)) {
              curr_stm_idx++;
            }
          }
        }
      }
      return true;
    }

    /**
     * @param BB Basic block of targeted function
     * @param hook Function to insert
     * @param insertStm Insertion point (enum)
     * @param localvar_map Values to store for each local from targeted fn scope
     * @param callInstFnName If insertion point is a call instruction, the point to insert
     */
    virtual bool runOnBasicBlockForFn(Function::iterator &BB, Function* hook,
        InsertStm insertStm, std::map<std::string, Value*> varname_ptr_map,
        std::string callInstFnName = "") {
      BasicBlock::iterator BFirst = BB->begin();
      BFirst++;
      for (BasicBlock::iterator BI = BB->begin(), BE = BB->end(); BI != BE; ++BI) {

        if (BI == BB->begin() && insertStm != kReturn && insertStm != kCall) {
          CallInst *newInst = getNewCallInst(hook, varname_ptr_map, BI);
          BB->getInstList().insert(BI, newInst);
        }

        if (isa<ReturnInst>(&(*BI)) && insertStm == kReturn) { // ignore insert location
          CallInst *newInst = getNewCallInst(hook, varname_ptr_map, BI);
           BB->getInstList().insert(BI, newInst);
        }

        if (isa<CallInst>(&(*BI)) && insertStm == kCall && !(callInstFnName.empty())) {
          CallInst *CI = dyn_cast<CallInst>(BI);
          if (CI->getCalledFunction()->getNameStr().compare(callInstFnName)) {
            continue;
          }
          CallInst *newInst = getNewCallInst(hook, varname_ptr_map, BI);
          BB->getInstList().insert(BI, newInst);
        }
      }

      return true;
    }

    CallInst* getNewCallInst(Function* hook, std::map<std::string, Value*> varname_ptr_map,
        Instruction *nextInst) {
      // TODO: FREAK OUT IF FIRST ARG ISN'T INT
      Value* intarg = ConstantInt::get(Type::getInt32Ty(getGlobalContext()), 1);
      std::vector<Value*> args_vt;
      args_vt.push_back(intarg);
      int i = 0;
      for (Function::arg_iterator arg_iter = hook->arg_begin();
          arg_iter != hook->arg_end(); ++arg_iter) {
        if (!(i++)) {
          continue;
        }
        // Add a load inst from the targeted fn's pointer ops
        // TODO: HANDLE WHEN ARG NOT FOUND IN FN
        std::map<std::string, Value*>::iterator varname_ptr_map_iter =
          varname_ptr_map.find(arg_iter->getNameStr());
        if (varname_ptr_map_iter == varname_ptr_map.end()) {
          // TODO: HANDLE?
          continue;
        }
        std::string tmp_arg_name = "_tmp_" + arg_iter->getNameStr();
        LoadInst *newLoadInst = new LoadInst(varname_ptr_map_iter->second,
            tmp_arg_name, nextInst);
        args_vt.push_back(newLoadInst);

      }
      // TODO: Better error logging
      assert(args_vt.size() == hook->getArgumentList().size()
          && "Argument list size of assert function does not match.");
      ArrayRef<Value*> *args_ra = new ArrayRef<Value*>(args_vt);
      return CallInst::Create(hook, *args_ra);
    }

  };
}

char TressaInsert::ID = 0;
static RegisterPass<TressaInsert> X("c-asserts", "Tressa (C)");


/** =====================
 *  TRESSA FOR C++
 *  ===================== */

namespace {
  struct TressaInsert2 : public ModulePass {
    static char ID;
    Function *hook_assert_class, *hook_assert_fn;
    TressaInsert2() : ModulePass(ID) { }

    virtual bool runOnModule(Module &M) {
      Constant *hookFunc;

      // Vector of fns for class/fns
      std::vector<Function*> class_fnvector;
      // Vector of pairs of classname/fnnames
      std::vector<std::vector<std::string> > class_fn_vt;
      // Vector of fns to run for fns
      std::vector<Function*> fnvector;
      // Vector of fnnames
      std::vector<std::string> fn_vt;

      // Strings
      // Asserts for class-less functions
      std::string assert_fn_prefix = "assertfn_fn_";
      std::string assert_class_fn_prefix = "assertfn_class_";

      // Information-gathering iteration.
      for (Module::iterator F = M.begin(), E = M.end(); F != E; ++F) {
        char* outbuf = (char*) std::malloc(sizeof F->getNameStr());
        int status = 0;
        demangleFunctionName(F, outbuf, &status);

        // Function asserts
        if (status == 0 &&
            !(std::string(outbuf).compare(0,
              assert_fn_prefix.size(), assert_fn_prefix))) {
          Function::ArgumentListType &argList = F->getArgumentList();
          int i = 0;
          std::vector<std::string> class_fn_pair;
          for (Function::ArgumentListType::iterator AI = argList.begin(),
              AE = argList.end(); AI != AE; ++AI, ++i) {
            fn_vt.push_back(AI->getNameStr());
            if (i == 0) {
              break;
            }
          }
          hookFunc = M.getOrInsertFunction(F->getName(),
              Type::getVoidTy(M.getContext()),
              Type::getInt32Ty(M.getContext()), (Type*) 0);
          hook_assert_fn = cast<Function>(hookFunc);
          fnvector.push_back(hook_assert_fn);
        }

        // Class asserts
        if (status == 0 &&
            !(std::string(outbuf).compare(0,
              assert_class_fn_prefix.size(), assert_class_fn_prefix))) {
          Function::ArgumentListType &argList = F->getArgumentList();
          int i = 0;
          std::vector<std::string> class_fn_pair;
          for (Function::ArgumentListType::iterator AI = argList.begin(),
              AE = argList.end(); AI != AE; ++AI, ++i) {
            class_fn_pair.push_back(AI->getNameStr());
            if (i == 1) {
              class_fn_vt.push_back(class_fn_pair);
              break;
            }
          }

          hookFunc = M.getOrInsertFunction(F->getName(),
              Type::getVoidTy(M.getContext()),
              Type::getInt32PtrTy(M.getContext()),
              Type::getInt32Ty(M.getContext()), (Type*) 0);
          hook_assert_class = cast<Function>(hookFunc);
          class_fnvector.push_back(hook_assert_class);
        }
      }

      // Code instrumentation iteration - for class-less functions.
      int fnvector_idx = 0;
      for (std::vector<std::string>::iterator VI = fn_vt.begin(),
          VE = fn_vt.end(); VI != VE; ++VI, fnvector_idx++) {
        for (Module::iterator F = M.begin(), E = M.end(); F != E; ++F) {
          char* outbuf = (char*) std::malloc(sizeof F->getNameStr());
          int status = 0;
          demangleFunctionName(F, outbuf, &status);
          if (status < 0 || outbuf == NULL
              || std::string(outbuf).compare(0, std::string(outbuf).find("("), *VI)) {
            continue;
          }
          for (Function::iterator BB = F->begin(), E = F->end(); BB != E; ++BB) {
            TressaInsert2::runOnBasicBlockForFn(BB, fnvector.at(fnvector_idx));
          }
        }
      }

      // Code instrumentation iteration - for classes and their functions.
      int class_fnvector_idx = 0;
      for (std::vector<std::vector<std::string> >::iterator VI = class_fn_vt.begin(),
        VE = class_fn_vt.end(); VI != VE; ++VI, class_fnvector_idx++) {
        std::vector<std::string> current_vt = *VI;
        std::string obj_name = current_vt.at(0);
        std::string fn_name = current_vt.at(1);
        for (Module::iterator F = M.begin(), E = M.end(); F != E; ++F) {
          // Check function name.
          char* outbuf = (char*) std::malloc(sizeof F->getNameStr());
          int status = 0;
          demangleFunctionName(F, outbuf, &status);
          if (status < 0 || outbuf == NULL
              || std::string(outbuf).compare(0, std::string(outbuf).find("("),
                obj_name + "::" + fn_name) != 0) {
          continue;
        }
          Function::ArgumentListType &argList = F->getArgumentList();
          std::string type_str;
          llvm::raw_string_ostream rso(type_str);
          bool filter_flag = false;
          Value* argobj = NULL;
          for (Function::ArgumentListType::iterator AI = argList.begin(),
            AE = argList.end(); AI != AE; ++AI) {
            AI->getType()->print(rso);
            StringRef arg_name = StringRef(rso.str());
            if (AI->getArgNo() == 0
                && AI->getName().equals("this")
                && arg_name.find("%class.") < std::string::npos
                && arg_name.find(obj_name) == arg_name.find("%class.") + 7
                && arg_name.size() == 7 + obj_name.size() + 1) {
              argobj = dyn_cast<Value>(AI);
              filter_flag = true;
            }
          }

          if (filter_flag && argobj != NULL
              && (size_t) class_fnvector_idx < class_fnvector.size()) {
            for (Function::iterator BB = F->begin(), E = F->end(); BB != E; ++BB) {
              TressaInsert2::runOnBasicBlock(BB, argobj,
                  class_fnvector.at(class_fnvector_idx));
            }
          }
        }
      }
      return true;
    }

    /**
     * Inserts {@param hook} function into the {@param BB} basic block.
     * For asserts on classes and their functions.
     */
    virtual bool runOnBasicBlock(Function::iterator &BB, Value* argobj, Function* hook) {
      for (BasicBlock::iterator BI = BB->begin(), BE = BB->end(); BI != BE; ++BI) {
        if (isa<ReturnInst>(&(*BI))) {
           ReturnInst *CI = dyn_cast<ReturnInst>(BI);
          Value* val =
            CastInst::CreatePointerCast(argobj,
                Type::getInt32PtrTy(getGlobalContext()), argobj->getName(), CI);
          Value* intarg = ConstantInt::get(Type::getInt32Ty(getGlobalContext()), 1);
          std::vector<llvm::Value*> args;
          args.push_back(val);
          args.push_back(intarg);
          CallInst *newInst = CallInst::Create(hook, args);
          newInst->setTailCall();
          BB->getInstList().insert((Instruction*) CI, newInst);
        }
      }
      return true;
    }

    /**
     * Inserts {@param hook} function into the {@param BB} basic block.
     * For asserts on class-less functions.
     */
    virtual bool runOnBasicBlockForFn(Function::iterator &BB, Function* hook) {
      for (BasicBlock::iterator BI = BB->begin(), BE = BB->end(); BI != BE; ++BI) {
        if (isa<ReturnInst>(&(*BI))) {
           ReturnInst *CI = dyn_cast<ReturnInst>(BI);
           Value* intarg = ConstantInt::get(Type::getInt32Ty(getGlobalContext()), 1);
           CallInst *newInst = CallInst::Create(hook, intarg);
           newInst->setTailCall();
           BB->getInstList().insert((Instruction*) CI, newInst);
        }
      }
      return true;
    }

    void demangleFunctionName(Function* F, char*& outbuf, int* status) {
      size_t length = 0;
      // outbuf will be null if the demangling is unsuccessful, and status will be < 0
      outbuf = abi::__cxa_demangle(F->getNameStr().c_str(), outbuf, &length, status);
    }
  };
}

char TressaInsert2::ID = 0;
static RegisterPass<TressaInsert2> B("cpp-asserts", "Tressa (C++)");


