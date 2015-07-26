-- Get all assertion predicates

import Data.List
import Data.Maybe
import Data.String
import System.Directory
import System.Environment
import System.FilePath



dirAsserts = "asserts/"
filePrefix = "xen-diff-"
fileSuffix = ".patch"
outFile = "hs-predicates.txt"


-- Enum for diff type
data DiffType = Same | Add | Del deriving (Show, Enum)

getAbsDirectoryContents :: FilePath -> IO [FilePath]
getAbsDirectoryContents dir =
  getDirectoryContents dir >>= mapM (canonicalizePath . (dir </>))

--processFileContents :: String -> IO()
processFileContents contents =
  mapM_ (\x -> putStrLn ("Line " ++ x)) contents
  where lineNum x = show $ fromJust $ elemIndex x contents

main :: IO()
main = do
  fileList0 <- getAbsDirectoryContents dirAsserts
  let fileList = drop 2 fileList0
  mapM_ processFile fileList
  where processFile theFile = do
          contents <- readFile theFile
          let fileLines = lines contents
          processFileContents fileLines


