-- Get distinct and alphabetically-sorted predicates in a file. Outputs to stdout.
-- In format ASSERT(...) with spaces removed.
--
-- To compile: ghc -O2 GetActivity.hs -o GetActivity
--
-- Usage Example: ./GetActivity sourcefile.c
--
-- Note on using with diff files (patches), same as GetPredicates:
--  1. This cannot handle huge files, so don't use on a complete git log.
--  2. It does not distinguish between +, -, or contextual (ie, unchanaged)
--      ASSERTS, so itsn't really ideal for a diff file anyway.
--  3. Since a diff is not the complete source code multiline asserts may
--      appear that are not closed. This breaks the searches for ) and produces
--      large, meaningless assertion predicates

import ProcessAsserts as P

import System.Environment

main :: IO()
main = do
  (filename:_) <- getArgs
  processFile filename

processFile :: String -> IO()
processFile theFile = do
  contents <- P.readFileAscii theFile
  let assertsLst = P.processFileContents $ lines contents
  let distinctLst = P.remDupsAndSort assertsLst
  putStrLn $ P.listToString distinctLst


