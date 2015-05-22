#include <assert.h>
#include <stdio.h>

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
  called_assert("fn3 => a1");
  assert(g_fn());
}

void assertfn_fn_4(int lastfn) {
  called_assert("lastfn (expected to fail)");
  assert(4 < 3);
}

void assertfn_fn_blahblahblah(int fn3) {
  called_assert("fn3 => a2");
  assert(fib_fn(3) > 1);
}

void assertfn_fn_blah2(int fn3) {
  called_assert("fn3 => a3");
  assert(2);
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
  printf("Called assert on %s\n", str);
}

