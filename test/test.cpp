#include "stdio.h"
#include <string>

struct type1
{
    int member1;
	int member2;
};

int main(int argc, char *argv[])
{
	type1 t;
	t.member1 = 1;
    printf("Hello, world.");
	std::string str;
    return 0;
}

#include "test2.h"

void main2()
{
	func();

    cls1 c1;
    c1.method();

    cls2 c2;
    c2.method();
}
