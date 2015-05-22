/**
 * Toy.cpp
 * 2015/05/22
 *
 * Instruments code to execute asserts at predefined points (in a separate .cpp file).
 *
 */


#define DEBUG_TYPE "toy"
#include <cxxabi.h>

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
  struct ToyInsert : public ModulePass {
    static char ID;
    Function *hook_assert_fn;
    ToyInsert() : ModulePass(ID) { }

    virtual bool runOnModule(Module &M) {
      Constant *hookFunc;

      // Vector of fns to run for fns
      std::vector<Function*> fnvector;
      // Vector of fnnames
      std::vector<std::string> fn_vt;

      // Strings
      // Asserts for class-less functions
      std::string assert_fn_prefix = "assertfn_fn_";

      // Information-gathering iteration.
      for (Module::iterator F = M.begin(), E = M.end(); F != E; ++F) {
        // Function asserts
        if (!(F->getNameStr().compare(0,
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
      }

      // Code instrumentation iteration.
      int fnvector_idx = 0;
      for (std::vector<std::string>::iterator VI = fn_vt.begin(),
          VE = fn_vt.end(); VI != VE; ++VI, fnvector_idx++) {
        for (Module::iterator F = M.begin(), E = M.end(); F != E; ++F) {
          if (F->getNameStr().compare(0, F->getNameStr().find("("), *VI)) {
            continue;
          }
          for (Function::iterator BB = F->begin(), E = F->end(); BB != E; ++BB) {
            ToyInsert::runOnBasicBlockForFn(BB, fnvector.at(fnvector_idx));
          }
        }
      }
      return true;
    }

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

  };
}

char ToyInsert::ID = 0;
static RegisterPass<ToyInsert> X("c-asserts", "Tressa (C)");


/** =====================
 *  TRESSA FOR C++
 *  ===================== */

namespace {
  struct ToyInsert2 : public ModulePass {
    static char ID;
    Function *hook_assert_class, *hook_assert_fn;
    ToyInsert2() : ModulePass(ID) { }

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
            ToyInsert2::runOnBasicBlockForFn(BB, fnvector.at(fnvector_idx));
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
              ToyInsert2::runOnBasicBlock(BB, argobj,
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

char ToyInsert2::ID = 0;
static RegisterPass<ToyInsert2> B("cpp-asserts", "Tressa (C++)");


