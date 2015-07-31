-- Get distinct predicates in this revision (patch file).

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


