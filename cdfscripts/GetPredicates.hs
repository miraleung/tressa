-- Get all assertion predicates of the form ASSERT(...)
-- of a patch file, and write them to a file.

import ProcessAsserts

import System.Environment
-- Main --
------------------------------------------

main :: IO()
main = do
  (filename:outFile:_) <- getArgs
  processFile filename outFile

processFile :: String -> String -> IO()
processFile theFile outFile = do
  contents <- readFileAscii theFile
  let assertsStr = processFileContents $ lines contents
  putStrLn $ (show (count "ASSERT" assertsStr)) ++ " asserts found"
  putStrLn assertsStr
  appendFile outFile assertsStr

