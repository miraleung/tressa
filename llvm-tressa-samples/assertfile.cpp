#include <cassert>
#include <iostream>
#include <string>
#include <stddef.h>
using namespace std;

void called_assert(string);

int f_fn(int*, int);
int fnfn(void);
int qfn(int*);

/**
 * @param Queue: Object (and named after) to run on
 * @param pop: Method to run on.
 */
void assertfn_class_somename(int* Queue2, int pop) {
  called_assert("Queue2::pop => a1");
  assert(Queue2 != NULL && "Queue2 is null");
}
void assertfn_class_2(int* Q, int push) {
  called_assert("Q::push");
  assert(qfn(Q));
}

void assertfn_class_3(int* Queue2, int pop) {
  called_assert("Queue2::pop => a2");
  assert(f_fn(Queue2, 9));
}

void assertfn_class_4(int* Queue2, int pop) {
  called_assert("Queue2::pop => a3");
  assert(4 % 2 == 0);
}

void assertfn_fn_1(int doit) {
  called_assert("doit (fn) a1");
  assert(1);
}

void assertfn_fn_2(int doit) {
  called_assert("doit (fn) => a2");
  assert(234);
}

void assertfn_fn_3(int doit2) {
  called_assert("doit2 (fn) => a1");
  assert(4 != 0);
}

// ============================


int qfn(int* obj) {
  return obj != NULL;
}

int fnfn() {
  return 1;
}

int f_fn(int* obj, int expr) {
  return *obj != expr;
}

// ============================

void called_assert(string str) {
  cout << "Called assert on " << str << endl;
}

