typedef struct { unsigned long t[2]; } timing;
#define timing_now(x) asm volatile(".byte 15;.byte 49" : "=a"((x)->t[0]),"=d"((x)->t[1]))
long long int getNow()
{
  timing now;
  timing_now(&now);
  return (long long int)now.t[0]+4294967296LL*(long long int)now.t[1];
}
