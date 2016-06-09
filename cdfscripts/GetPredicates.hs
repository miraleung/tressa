-- Get all assertion predicates of the form ASSERT(...)
-- of a source file, and APPEND them to an output file.
-- Additionally, print to stdout, preceded by the assertions count.
-- All spaces and newlines are removed, as well as any + or - at the beginning
-- of a line (in the case of patch/diff files).
-- 
-- To compile: ghc -O2 GetPredicates.hs -o GetPredicates
--
-- Usage Example: ./GetPredicates sourcefile.c predicates.out
-- Produces predicates.out file containg all ASSERT(...) statements
--
-- Note on using with diff files (patches):
--  1. This cannot handle huge files, so don't use on a complete git log.
--  2. It does not distinguish between +, -, or contextual (ie, unchanaged)
--      ASSERTS, so itsn't really ideal for a diff file anyway.
--  3. Since a diff is not the complete source code multiline asserts may
--      appear that are not closed. This breaks the searches for ) and produces
--      large, meaningless asserton predicates

import ProcessAsserts as P

import System.Environment
-- Main --
------------------------------------------

main :: IO()
main = do
  (filename:outFile:_) <- getArgs
  processFile filename outFile

processFile :: String -> String -> IO()
processFile theFile outFile = do
  contents <- P.readFileAscii theFile
  let assertsLst = P.processFileContents $ lines contents
  let assertsStr = P.listToString assertsLst
  putStrLn $ (show (length assertsLst)) ++ " asserts found"
  putStrLn assertsStr
  appendFile outFile assertsStr

