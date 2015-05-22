#include <iostream>
using namespace std;

class Queue
{
public:
  Queue();
  ~Queue();
  void push(int);
  int pop();
  void print();
private:
  typedef struct Node {
    Node *next;
    int data;
  } NODE;
  NODE* head;
};

Queue::Queue()
{
  head = NULL;
}

Queue::~Queue()
{
  if(head == NULL) return;
  NODE *cur = head;
  while(cur) {
    Node *ptr = cur;
    cur = cur->next;
    delete ptr;
  }
}

void Queue::push(int n)
{
  if(head == NULL) {
    head = new NODE;
    head->data = n;
    head->next = NULL;
    return;
  }
  NODE *cur = head;
  while(cur) {
    if(cur->next == NULL) {
      NODE *ptr = new NODE;
      ptr->data = n;
      ptr->next = NULL;
      cur->next = ptr;
      return;
    }
    cur = cur->next;
  }
}

void Queue::print()
{
  if(head==NULL) return;
  Node *cur = head;
  while(cur) {
    cout << cur->data << " ";
    cur = cur->next;
  }
  cout << endl;
}

int Queue::pop()
{
  if(head == NULL) {
    cout << "empty estack!" << endl;
    return NULL;
  }
  NODE *tmp = head;
  int value = head->data;
  if(head->next) {
    head = head->next;
  }
  // pop the last element (head)
  else {
    delete tmp;
    head = NULL;
  }
  cout << "pop: " << value << endl;;
  return value;
}

// =======================================

class Queue2
{
public:
  Queue2();
  ~Queue2();
  void push(int);
  int pop();
  void print();
private:
  typedef struct Node {
    Node *next;
    int data;
  } NODE;
  NODE* head;
};

Queue2::Queue2()
{
  head = NULL;
}

Queue2::~Queue2()
{
  if(head == NULL) return;
  NODE *cur = head;
  while(cur) {
    Node *ptr = cur;
    cur = cur->next;
    delete ptr;
  }
}

void Queue2::push(int n)
{
  if(head == NULL) {
    head = new NODE;
    head->data = n;
    head->next = NULL;
    return;
  }
  NODE *cur = head;
  while(cur) {
    if(cur->next == NULL) {
      NODE *ptr = new NODE;
      ptr->data = n;
      ptr->next = NULL;
      cur->next = ptr;
      return;
    }
    cur = cur->next;
  }
}

void Queue2::print()
{
  if(head==NULL) return;
  Node *cur = head;
  while(cur) {
    cout << cur->data << " ";
    cur = cur->next;
  }
  cout << endl;
}

int Queue2::pop()
{
  if(head == NULL) {
    cout << "empty estack!" << endl;
    return NULL;
  }
  NODE *tmp = head;
  int value = head->data;
  if(head->next) {
    head = head->next;
  }
  // pop the last element (head)
  else {
    delete tmp;
    head = NULL;
  }
  cout << "pop: " << value << endl;;
  return value;
}

// =======================================
class Q
{
public:
  Q();
  ~Q();
  void push(int);
  int pop();
  void print();
private:
  typedef struct Node {
    Node *next;
    int data;
  } NODE;
  NODE* head;
};

Q::Q()
{
  head = NULL;
}

Q::~Q()
{
  if(head == NULL) return;
  NODE *cur = head;
  while(cur) {
    Node *ptr = cur;
    cur = cur->next;
    delete ptr;
  }
}

void Q::push(int n)
{
  if(head == NULL) {
    head = new NODE;
    head->data = n;
    head->next = NULL;
    return;
  }
  NODE *cur = head;
  while(cur) {
    if(cur->next == NULL) {
      NODE *ptr = new NODE;
      ptr->data = n;
      ptr->next = NULL;
      cur->next = ptr;
      return;
    }
    cur = cur->next;
  }
}

void Q::print()
{
  if(head==NULL) return;
  Node *cur = head;
  while(cur) {
    cout << cur->data << " ";
    cur = cur->next;
  }
  cout << endl;
}

int Q::pop()
{
  if(head == NULL) {
    cout << "empty estack!" << endl;
    return NULL;
  }
  NODE *tmp = head;
  int value = head->data;
  if(head->next) {
    head = head->next;
  }
  // pop the last element (head)
  else {
    delete tmp;
    head = NULL;
  }
  cout << "pop: " << value << endl;;
  return value;
}


// =======================================

void doit(const std::string& s) {
  cout << "doit " << s << "\n";
}

int doit2(int x) {
  return x+234;
}


int main()
{
  Queue *que = new Queue();
  que->push(10);
  que->push(20);
  que->push(30);
  que->push(40);
  que->push(50);
  que->print();
  que->pop();que->print();
  que->pop();que->print();
  que->pop();que->print();
  que->pop();que->print();
  que->pop();que->print();
  que->pop();que->print();

  cout << "======== Do Queue2 ========\n";

  Queue2 *que2 = new Queue2();
  que2->push(10);
  que2->push(20);
  que2->push(30);
  que2->push(40);
  que2->push(50);
  que2->print();
  que2->pop();que2->print();
  que2->pop();que2->print();
  que2->pop();que2->print();
  que2->pop();que2->print();
  que2->pop();que2->print();
  que2->pop();que2->print();

  cout << "======== Do Q ========\n";

  Q *q = new Q();
  q->push(10);
  q->push(20);
  q->push(30);
  q->push(40);
  q->push(50);
  q->print();
  q->pop();q->print();
  q->pop();q->print();
  q->pop();q->print();
  q->pop();q->print();
  q->pop();q->print();
  q->pop();q->print();

  cout << "======== Done queue stuff ========\n";
  cout << "Call doit2\n";
  doit2(2);
  cout << "Call doit\n";
  doit("asdf");
  return 0;
}
