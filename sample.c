#include <stdio.h>
#include <stdbool.h>
#include <assert.h>

void fn1(void);
int fn2(void);
int fn3(int x);

void donothing(void);
void doit(void);
int doita(void);
char doitRK(void);
bool someotherfn(int, int);
char lastfn(void);

int main() {

  printf("Called main\n");
  fn1();
  fn2();
  fn3(3);
  donothing();
  doita();
  doitRK();
  doit();
  someotherfn(23, 45);
  lastfn();
  return 1;
}

void fn1() {
  printf("call to fn1\n");
}

int fn2() {
//  donothing();
  printf("call to fn2\n");
  assert(1 != 0);
  return 2;
}


int fn3(int x) {
//  donothing();
  printf("call to fn3\n");
  return x+1;
}

void donothing() {
  printf("call to donothing\n");
}

void doit() {
  printf("called doit\n");
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


