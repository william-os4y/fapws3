#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <signal.h>
#include <assert.h>
#include <ctype.h>
#include "extra.h"



/*
This procedure remove the character c from source s and put the result in destination d
*/
void stripChar(char *s, char *d, char c) {
    while (*s) { 
        if (*s != c) { *d++ = *s; }
        s++;  
    }
    *d = '\0';
}

/*
HTML decoder procedure we can use for uri or post parameters. It return a char which must be free'd in the caller
*/
char *
decode_uri(const char *uri)
{
    char c, *ret;
    int i, j;
    
    ret = malloc(strlen(uri) + 1);
    for (i = j = 0; uri[i] != '\0'; i++) {
        c = uri[i];
        if (c == '+') {
            c = ' ';
        } else if (c == '%' && isxdigit((unsigned char)uri[i+1]) &&
            isxdigit((unsigned char)uri[i+2])) {
            char tmp[] = { uri[i+1], uri[i+2], '\0' };
            c = (char)strtol(tmp, NULL, 16);
            i += 2;
        }
        ret[j++] = c;
    }
    ret[j] = '\0';
    
    return (ret);
}


/*
this procefure remove spaces and tabs who could lead or end a string
*/
char * remove_leading_and_trailing_spaces(char* s)
{ 
    int start=0;
    int end=(int)strlen(s);
  
    //remove trailing blanks
    while(end>0 && (s[end-1]==' ' || s[end-1]=='\t'))
    {
        end--;
    }
    s[end]='\0';
    //remove leading blanks
    while(start<end && (*s==' ' || *s=='\t'))
    {
        s++;
        start++;
    }
    return s;
}
