#define _POSIX_C_SOURCE 199309L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
typedef void (*ksf)(const uint16_t*, uint16_t*);
void ks_std(const uint16_t*, uint16_t*); void ks_v2(const uint16_t*, uint16_t*); void ks_v3(const uint16_t*, uint16_t*); void ks_null(const uint16_t*, uint16_t*); void ks_v3_inv(uint16_t*);
static int cmp(const void*a,const void*b){double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);}
int main(int argc,char**argv){
    if(argc>1 && !strcmp(argv[1],"dump")){            /* read keys.bin (N x 4 uint16), write rk_v3.bin (N x 32) and check inverse */
        FILE*f=fopen("keys.bin","rb"),*o=fopen("rk_v3.bin","wb"); uint16_t mk[4],rk[32],r2[32]; long bad=0,n=0;
        while(fread(mk,2,4,f)==4){ ks_v3(mk,rk); fwrite(rk,2,32,o); memcpy(r2,rk,64); memset(r2,0,56); ks_v3_inv(r2); bad+=memcmp(r2,rk,64)!=0; n++; }
        printf("dumped %ld keys; inverse-schedule mismatches: %ld\n",n,bad); return 0; }
    enum{NK=65536,REP=1000000,RUNS=15}; static uint16_t keys[NK][4]; uint16_t rk[32]; uint32_t s=20261126u; volatile uint16_t sink=0;
    for(int i=0;i<NK;i++)for(int j=0;j<4;j++){ s^=s<<13; s^=s>>17; s^=s<<5; keys[i][j]=(uint16_t)s; }
    ksf F[4]={ks_null,ks_std,ks_v2,ks_v3}; const char*N[4]={"baseline","ks_std","ks_v2","ks_v3"}; static double T[4][RUNS];
    for(int run=-1;run<RUNS;run++) for(int k=0;k<4;k++){ struct timespec a,b; clock_gettime(CLOCK_MONOTONIC,&a);
        for(int i=0;i<REP;i++){ F[k](keys[i&(NK-1)],rk); sink^=rk[3]; }
        clock_gettime(CLOCK_MONOTONIC,&b); if(run>=0) T[k][run]=((b.tv_sec-a.tv_sec)*1e9+(b.tv_nsec-a.tv_nsec))/REP; }
    double med[4]; for(int k=0;k<4;k++){ qsort(T[k],RUNS,sizeof(double),cmp); med[k]=T[k][RUNS/2]; printf("%-9s median %7.2f ns [min %.2f max %.2f]\n",N[k],med[k],T[k][0],T[k][RUNS-1]); }
    printf("ratio to std (baseline subtracted): v2 %.2f  v3 %.2f\n",(med[2]-med[0])/(med[1]-med[0]),(med[3]-med[0])/(med[1]-med[0])); return sink&0; }
