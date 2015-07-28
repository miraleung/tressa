-- Get all assertion predicates of the form ASSERT(...)

import Prelude hiding (catch)

import Control.Applicative
import Control.Exception
import Data.Char
import Data.List
import Data.Maybe
import Data.String
import System.Directory
import System.Environment
import System.FilePath
import System.IO.Error hiding (catch)
import Text.Regex.TDFA

import qualified Data.ByteString.Char8 as B


dirAsserts = "test-asserts/"
filePrefix = "xen-diff-"
fileSuffix = ".patch"
tmpOutFile = "tmp-hs-predicates.txt"
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

readFileAscii :: String -> IO String
readFileAscii path = B.unpack <$> B.map (clearChar '-') <$> B.readFile path
  where clearChar :: Char -> Char -> Char
        clearChar d c
          | c == '\r' || c == '\n' = c
          | c >= '\32' && c < '\128' = c
          | otherwise = d

removeFileIfExists :: FilePath -> IO ()
removeFileIfExists fileName = removeFile fileName `catch` handleExists
  where handleExists e
          | isDoesNotExistError e = return ()
          | otherwise = throwIO e

parensDelta :: String -> Int
-- Returns (#left parens - # right parens)
parensDelta =
  foldl (\x y ->
  case () of _ | y == '(' -> x + 1 | y == ')' -> x - 1 | otherwise -> x + 0) 0

isFullAssert :: String -> Bool
-- Returns true if {@code str} is a completed assert statement.
isFullAssert str = (0 == parensDelta str) && (regexMatch (normalize str) patAssertHead)

isHeaderAssert :: String -> Bool
-- Returns true if {@code str} is the start of an assert statement
-- and is incomplete.
isHeaderAssert str = (0 < parensDelta str) && (regexMatch (normalize str) patAssertHead)

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
strip chr = filter (/= chr)

stripSpace :: String -> String
stripSpace = strip ' '

-- Returns true if the line is a +/-/same in the diff
isAdd :: String -> Bool
isDel :: String -> Bool
isSame :: String -> Bool
isAdd str = (str !! 0) == '+'
isDel str = (str !! 0) == '-'
isSame str = (str !! 0) /= '+' && (str !! 0) /= '-'

normalize :: String -> String
-- Strip whitespaces and starting +/-, if any
normalize str =  stripSpace $ stripDiffChar $ delete '\\' str

stripDiffChar :: String -> String
stripDiffChar str | isAdd str || isDel str = tail str | otherwise = str

-- -- List utilities -- --
remDupsAndSort :: (Ord a) => [a] -> [a]
remDupsAndSort = map head . group . sort

elemIndexEnd :: Char -> String -> Int
elemIndexEnd chr str = (length str) - (fromJust $ elemIndex chr $ reverse str)

sublist :: Int -> Int -> [a] -> [a]
sublist start end lst = drop start $ take end lst



-- Processors --
------------------------------------------

procMlAsserts :: [String] -> [String]
procMlAsserts asserts = procMlAsserts' asserts [] ""

procMlAsserts' :: [String] -> [String] -> String -> [String]
-- Args: array of strings to process, accumulator, interim (temp) assert stub
procMlAsserts' [] acc _ = acc
procMlAsserts' (x:xs) [] stubvar =
  if isHeaderAssert x || isFullAssert x
    then procMlAsserts' xs [x] stubvar
    else procMlAsserts' xs [] stubvar
procMlAsserts' (x:xs) (a:acc) stubvar
  | isHeaderAssert x || isFullAssert x = procMlAsserts' xs (x:a:acc) stubvar
  | not (null stubvar) && isAdd x = procMlAsserts' xs ((stubvar ++ (normalize x)) : (a: acc)) ""
  | isHeaderAssert a && isSame a && isDel x && null stubvar =
    procMlAsserts' xs ((a ++ (normalize x)) : acc) a
  | otherwise = procMlAsserts' xs (a : acc) stubvar


filterOutBadStms :: [String] -> [String]
filterOutBadStms stmlst = stmlst \\ badLst
  where cmtPatAdd = "^\\+?(//|\\*)"
        cmtPatDel = "^\\-(//|\\*)"
        diffHeaderPat = "^\\-\\-(a|/dev/null)|\\+\\+b"
        diffHeaderPat2 = "^(@@.*@@|diff.*r|^#)"
        emptyLinePat = "^$"
        lineCmtPat = "^/\\*"
        bracketPat = "^\\{|\\}"
        stmPat = "^if\\(|else|for\\(|printk\\(|while|return|switch|do{|break|continue "
        declPat = "^(char|int|unsigned|long|struct|extern|static|void|u32)"
        otherPat = "^\"|[A-Z]_ASSERT|ASSERT_[A-Z]"
        badPatLst = [cmtPatAdd, cmtPatDel, diffHeaderPat, diffHeaderPat2,
          lineCmtPat, bracketPat, stmPat, declPat, emptyLinePat, otherPat]
        badLst = filter (\x ->
          foldl (\y z -> y || regexMatch (normalize x) z) False badPatLst) stmlst


filterForAssertsAndConts :: [String] -> [String]
filterForAssertsAndConts contents = filteredLst
  where lst0 = filterOutBadStms contents
        filteredLst = map (\x -> strip '\\' x) lst0

--processMultilineAsserts :: [(Int, String)] -> [(Int, String)]
-- Map of incomplete assert headers and
--processMultilineAsserts themap

--processFileContents :: String -> IO()
processFileContents contents = do
  putStrLn $ (show (length assertsLst)) ++ " asserts found"
  putStrLn assertsStr
  appendFile tmpOutFile assertsStr
  where txtLst0 = filterForAssertsAndConts contents
        fullAssertsLst = filter (\x -> isFullAssert x) txtLst0
        multilineAssertsLst = procMlAsserts (txtLst0 \\ fullAssertsLst)
        txtLst1 = fullAssertsLst ++ multilineAssertsLst
        assertsLst = map (\x -> sublist 0 (elemIndexEnd ')' (normalize x)) (normalize x)) txtLst1
        assertsStr = foldr (\x y -> x ++ y) "" $ map (\z -> z ++ "\n") assertsLst


-- Main --
------------------------------------------

main :: IO()
main = do
  fileList0 <- getAbsDirectoryContents dirAsserts
  let fileList = drop 2 fileList0
  mapM_ processFile fileList
  unsortedAsserts <- readFile tmpOutFile
  let sortedAsserts = remDupsAndSort unsortedAsserts
  removeFileIfExists outFile
  writeFile outFile sortedAsserts
  removeFile tmpOutFile
  where processFile theFile = do
          putStrLn ("Processing " ++ drop (elemIndexEnd '/' theFile) theFile)
          contents <- readFileAscii theFile
          let fileLines = lines contents
          processFileContents fileLines


