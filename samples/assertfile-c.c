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

void assertfn_fn_1(int doit) {
  called_assert("doit => a1");
  assert(f_fn());
}

void assertfn_fn_2(int someotherfn) {
  called_assert("someotherfn => a1");
  assert(134);
}

void assertfn_fn_3(int fn3) {
//  int _assertfn_fn_3_ifexpr_0;
//  int _assertfn_fn_3_ifexpr;
  int _assertfn_fn_3_ifexpr_1;
//  int _assertfn_fn_3_return;
  called_assert("fn3 => a1");
  assert(g_fn());
}

void assertfn_fn_4(int lastfn) {

  called_assert("lastfn (expected to fail)");
  assert(4 < 3);
}

void assertfn_fn_blahblahblah(int donothing) {
  int _assertfn_fn_blahblahblah_call_printf;
  called_assert("donothing => assert");
  assert(fib_fn(3) > 1);
}

void assertfn_fn_blah2(int fn3) {
  called_assert("fn3 => a3");
  assert(2);
}

// fn2 is the name of the targeted function
// This assertfn must be prefixed with "assertfn_fn_", but
// the subsequent identifier is arbitrary, as long as it is unique.
void assertfn_fn_foo(int fn2) {
  called_assert("foo assert");
  // Locals in fn2
  char ch;
  int i = 0;
  int intptr;
  // Insertion point b/c prefixed with same assertfn name
  // one of call_<fnname>, return, for_<# of completed block>, if_<# of completed block>
  int _assertfn_fn_foo_for_0;

//  int arg;
//  assert(arg);
//  int *intptr = NULL;
//  assert(fn3(i) > 2);
  assert(GLOBAL_VAR_1 == 1234);
  printf("\t\t value of intptr: %d\n", intptr);
  assert(foobar(intptr, i));
  assert(barfoo(ch) == ('a' - '0'));
  printf("\t\t assertfn_fn_fn2: Value of i is %d\n", i);
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

