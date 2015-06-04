#include "sample.h"

int main() {

  printf("Called main\n");
  fn1();
  fn2(1);
  fn3(3);
  donothing();
  doita();
  doitRK();
  doit();
  someotherfn(23, 45);
  lastfn();
  return 1;
}

int foobar(int ptr, int val) {
  return !(ptr % 10);
}

int barfoo(char c) {
  return c - '0';
}

void fn1() {
  printf("call to fn1\n");
}

int fn2(int arg) {
//  donothing();
  printf("call to fn2\n");
  int i = 5;
  int intptr;
  intptr = 100;
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
    printf("In fn2's second if stm.\n");
  }

  printf("\tforloop: ");
  int k;
  for (k = 0; k < 3; k++) {
    printf("  k=%d", k);
  }
  printf("Done for loop in fn2 \n");

  return 2;
}


int fn3(int x) {
//  donothing();
  printf("call to fn3\n");
  if (x) {
    printf("first if of fn3\n");
  }

  if (x+1) {
    printf("second if of fn3\n");
  }

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
    return x+1;
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

char lastfn() {
  printf("called last fn\n");
  return 'b';
}


