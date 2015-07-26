-- Get all assertion predicates

import Data.List
import Data.Maybe
import Data.String
import System.Directory
import System.Environment
import System.FilePath

import Text.Regex.TDFA


dirAsserts = "asserts/"
filePrefix = "xen-diff-"
fileSuffix = ".patch"
outFile = "hs-predicates.txt"

patAssertHead = "^.*ASSERT\\(.*$"


-- Enum for diff type
data DiffType = Same | Add | Del deriving (Show, Enum)

regexMatch input pat = input =~ pat :: Bool


-- Utilities --
------------------------------------------

getAbsDirectoryContents :: FilePath -> IO [FilePath]
getAbsDirectoryContents dir =
  getDirectoryContents dir >>= mapM (canonicalizePath . (dir </>))

parensDelta :: String -> Int
-- Returns (#left parens - # right parens)
parensDelta =
  foldl (\x y ->
  case () of _ | y == '(' -> x + 1 | y == ')' -> x - 1 | otherwise -> x + 0) 0

isFullAssert :: String -> Bool
-- Returns true if {@code str} is a completed assert statement.
isFullAssert str = (0 == parensDelta str) && (regexMatch str patAssertHead)

isHeaderAssert :: String -> Bool
-- Returns true if {@code str} is the start of an assert statement
-- and is incomplete.
isHeaderAssert str = (0 < parensDelta str) && (regexMatch str patAssertHead)

-- -- List/tuple utilities -- --
pairFirst :: (a, b) -> a
pairFirst (a, _) = a

pairSecond :: (a, b) -> b
pairSecond (_, b) = b

mapKeyGet :: (Eq a) => a -> [(a, b)] -> b
mapKeyGet key theMap = pairSecond $ head (filter (\x -> key == pairFirst x) theMap)

-- Returns first one matching the value
mapValueGet ::(Eq b) =>  b -> [(a, b)] -> a
mapValueGet val theMap = pairFirst $ head (filter (\x -> val == pairSecond x) theMap)

-- -- String utilities -- --
strip :: Char -> String -> String
strip chr str = filter (\x -> x /= chr) str

stripSpace :: String -> String
stripSpace = strip ' '


-- Processors --
------------------------------------------

filterForAssertsAndConts :: [String] -> [(Int, String)]
filterForAssertsAndConts contents =
  zip (map (\x -> fromJust (elemIndex x contents)) assertLst) assertLst
  where pat = "^[^@@.*@@][^diff.*r][^#.*define.*]"
        cmtPatAdd = "^\\+?(//|\\*)"
        cmtPatDel = "^\\-(//|\\*)"
        noSpaceStr = stripSpace
        isNotComment str = not (regexMatch str cmtPatAdd)
          && not (regexMatch str cmtPatDel)
        lambdafn = (\x -> (regexMatch x pat)
          && (isHeaderAssert x || isFullAssert x || 0 > parensDelta x)
          && isNotComment (noSpaceStr x))
        assertLst = filter lambdafn contents

--processFileContents :: String -> IO()
processFileContents contents =
  mapM_ (\x -> putStrLn ((show $ pairFirst x) ++ "\t" ++ (pairSecond  x))) finalMap
  where map0 = filterForAssertsAndConts contents
        finalMap = filter (\x -> isFullAssert (pairSecond x)) map0


-- Main --
------------------------------------------

main :: IO()
main = do
  fileList0 <- getAbsDirectoryContents dirAsserts
  let fileList = drop 2 fileList0
  mapM_ processFile fileList
  where processFile theFile = do
          contents <- readFile theFile
          let fileLines = lines contents
          processFileContents fileLines


