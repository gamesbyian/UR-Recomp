#include <assert.h>
#include <stdint.h>
#include <stdio.h>
// Minimal direct transcription of ur_controller_seat_choose, taken, vacated
// from PR #2198 f3c6db0, used to reproduce the same-key ambiguity.
typedef struct {int enabled,occupied;uint64_t absent_owner_key;} Seat;
int vacant(const Seat s[2],int i){return i>=0&&i<2&&s[i].enabled&&!s[i].occupied;}
int choose(const Seat s[2],uint64_t key,int idx,int forced){
 if(forced>=0)return vacant(s,forced)?forced:-1;
 if(key)for(int i=0;i<2;i++)if(vacant(s,i)&&s[i].absent_owner_key==key)return i;
 if(vacant(s,idx)&&s[idx].absent_owner_key==0)return idx;
 for(int i=0;i<2;i++)if(vacant(s,i)&&s[i].absent_owner_key==0)return i;
 for(int i=0;i<2;i++)if(vacant(s,i))return i;
 return -1;
}
void taken(Seat s[2],int i,uint64_t key){for(int j=0;j<2;j++)if(key&&s[j].absent_owner_key==key)s[j].absent_owner_key=0;s[i].occupied=1;s[i].absent_owner_key=0;}
void vacated(Seat s[2],int i,uint64_t key){s[i].occupied=0;s[i].absent_owner_key=key;}
int main(void){Seat s[2]={{1,0,0},{1,0,0}};uint64_t key=0x1234;
 int a=choose(s,key,0,-1);taken(s,a,key);
 int b=choose(s,key,1,-1);taken(s,b,key);
 vacated(s,a,key);vacated(s,b,key);
 int b_return=choose(s,key,1,-1);taken(s,b_return,key);
 int a_return=choose(s,key,0,-1);taken(s,a_return,key);
 printf("initial: A=%d B=%d; after B-first reconnect: B=%d A=%d\n",a,b,b_return,a_return);
 assert(a==0&&b==1&&b_return==0&&a_return==1);
 return 0;}
