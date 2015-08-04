#include <assert.h>
#include <stdio.h>

// All globals and function headers in targeted source code
// must be in header file here.
#include "sample.h"

// Assumptions:
// All globals in .h file

void called_assert(char*);
int f_fn(void);
int g_fn(void);
int fib_fn(int);

/**
 * @param Queue: Object (and named after) to run on
 * @param pop: Method to run on.
 */

void _assertfn_for_ascii_fn(int ints_to_ascii_char, int _tressa_return_0, int x, int y) {
  assert(x && !(y % 2) && (32 <= (x + y) <= 126));
}


void _assertfn_fn_1(int doit, int _tressa_return_0) {
  called_assert("doit => a1");
  assert(f_fn());
}

void _assertfn_2(int someotherfn, int _tressa_return_0) {
  called_assert("someotherfn => a1");
  assert(134);
}

void _assertfn_3(int fn3, int _tressa_if_2, int _tressa_for_2) {
  called_assert("fn3 => a1");
  assert(g_fn());
}

void _assertfn_4(int lastfn, int _tressa_if_0) {
  called_assert("lastfn (expected to fail)");
  assert(4 < 3);
}

void _assertfn_fn_blahblahblah(int donothing, int _tressa_call_printf) {
  called_assert("donothing => assert");
  assert(fib_fn(3) > 1);
}

void _assertfn_fn_blah2(int fn3, int x, int _tressa_return_1, int i) {
  called_assert("fn3 => a3");
  assert(2);
  printf("\t\t value of i is %d, x = %d\n", i, x);
}

// fn2 is the name of the targeted function
// This _assertfn must be prefixed with "_assertfn_fn_", but
// the subsequent identifier is arbitrary, as long as it is unique.
void _assertfn_foo(int fn2, int i, char ch, int *intptr,
    int _tressa_if_0, int arg, int *y, int _tressa_return_0) {
  called_assert("foo assert");
  // Insertion point b/c prefixed with same _assertfn name
  // one of call_<fnname>, return, for_<# of completed block>, if_<# of completed block>

//  assert(fn3(i) > 2);
  printf("\t\t arg is %d, y is %d\n", arg, *y);
  assert(GLOBAL_VAR_1 == 1234);
  printf("\t\t value of intptr: %d\n", *intptr);
  assert(foobar(intptr, i));
  assert(barfoo(ch) == ('a' - '0'));
  printf("\t\t _assertfn_fn_fn2: Value of i is %d\n", i);
  assert(arg);

}


// ====================

int f_fn() {
  return 3 % 2 ;
}

int g_fn() {
  return 4 > 0;
}

int fib_fn(int x) {
  if (x <= 2) return 1;
  return fib_fn(x - 1) + fib_fn(x - 2);
}

// =====================

void called_assert(char* str) {
  printf("\t~~~ Called assert on %s ~~~\n", str);
}

