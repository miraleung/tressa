#include <stdlib.h>

#include "sample.h"

#define ABS(x) (((x) < 0) ? -(x) : (x))

int main() {
  int something = 2341;
  int *ptr = &something;
  printf("Called main\n");
  fn1();
  fn2(234, ptr);
  fn3(3);
  donothing();
  doita();
  doitRK();
  doit();
  someotherfn(23, 45);
  lastfn();
  printf("\n\nFoo: %c\n", ints_to_ascii_char(35, 30));
  return 1;
}

int foobar(int *ptr, int val) {
  return !(*ptr % 10);
}

int barfoo(char c) {
  return c - '0';
}

void fn1() {
  printf("call to fn1\n");
}

int fn2(int arg, int *y) {
//  donothing();
  printf("call to fn2\n");
  int i = 5;
  int contents = 1230;
  int *intptr = &contents;

  printf("here\n");
  char ch = 'a';
  // Insert assert(i > 2)
  printf("\tGlobals: %d; %d\n", GLOBAL_VAR_1, GLOBAL_VAR_2);
  if (fn3(i) > 3) {
    printf("Leaving fn2's if stm.\n");
  } else {
    printf("Leaving else bch of if stm of fn2\n");
  }

  printf("Done first ifstm of fn2\n");
  if (fn3(i)) {
    printf("In fn2's  asdf second if stm.\n");
  }

  printf("\tforloop: ");
  int k;
  for (k = 0; k < 3; k++) {
    i += 20;
    printf("  k=%d, i=%d;", k, i);
  }
  printf("Done for loop in fn2 \n");

  return 2;
}


int fn3(int x) {
//  donothing();
  int local;
  int *ptr1 = NULL;
  int anothervar = 2341;
  int somevar = 4564;
  int *ptr0 = &anothervar;
  printf("call to fn3\n");
  if (x) {
    printf("first if of fn3\n");
  }

  local = anothervar;
  *ptr0 = somevar;
  if (rand() % 2) {
    printf("second if of fn3\n");
    if (rand() % 3) {
      printf("third nested if\n");
    }
    return 1;
  }

  int r, k, t;
  int temp = 0;
  for (r = 0; r < 3; r++)
    for (k = 0; k < 3; k++)
      for (t = 0; t < 3; t++)
        temp++;

  if (1) {
    printf("third if of fn3\n");
    int i;
    printf("\tforloop fn3:\n");
    for (i = 0; i < 3; i++) {
      if (i) {
        printf("\t\tif:  i=%d\n", i);
      }
      printf("\tout of nested if in for for fn3\n");
    }
    printf("\n");
  }
  return x+1;
}

void donothing() {
  printf("call to donothing\n");
}

void doit() {
  printf("called doit\n");
  int i = 20;
  if (i % 2 == 0) {
    printf("In if stm of doit\n");
  }
}

int doita() {
  printf("called doita\n");
  int i = 2 + (someotherfn(2, 0) ? 234 : 0);
  return i;
}

char doitRK() {
  printf("called doitRK\n");
  return 'a';
}

bool someotherfn(int a, int b) {
  printf("called someotherfn\n");
  return a + b > 0;
}

char ints_to_ascii_char(int x, int y) {
  // Assert that x is non-zero, y is even, and both
  // put together are in the range [32, 126] (ASCII char)
  return x + y - 48 + '0';
}



char lastfn() {
  printf("called last fn\n");
  int x = 100;
  int y = ABS(x);
  printf("MACRO CALL: %d", x);
  if (1) {
    return 'c';
  }
  return 'b';
}


