#include <time.h>
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


/*
This procedure append text to data and return the result in new buffer to free!!!! 
return NULL in case of trouble
*/
char *str_append( char *data, char *text)
{
    char *result;
    int data_len, text_len;
    data_len = strlen(data);
    text_len = strlen(text);
     
    result = realloc( data, (data_len + text_len + 1));
    if (result == NULL) 
       return NULL;
    memcpy (result + data_len, text, text_len + 1);
    result[data_len + text_len + 1] = '\0';
    return result;
}


/*
Provide a string representation of the current time
*/
char *cur_time(char *fmt)
{
    int len=200;
    char *outstr;
    time_t t;
    struct tm *tmp;
   
    outstr=malloc(len);
    t = time(NULL);
    tmp = gmtime(&t);
    if (tmp == NULL) {
        perror("gmtime");
        return NULL;
    }

    if (strftime(outstr, len, fmt, tmp) == 0) { //this is the time format taken from lighttpd
        fprintf(stderr, "strftime returned 0");
        return NULL;
    }

    //printf("Result string is \"%s\"\n", outstr);
    return outstr;
} /* main */



char *time_rfc1123(time_t t)
{
    char *days_names[] ={ "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" };
    char *month_names[] ={ "Jan", "Feb", "Mar", "Apr", "May", "Jun","Jul", "Aug", "Sep", "Oct", "Nov", "Dec" };
    const int date_len = 29;
    struct tm *tmp;
    char *outstr = malloc(date_len+1);

    tmp=gmtime(&t);
    strftime(outstr, date_len+1, "---, %d --- %Y %H:%M:%S GMT", tmp); //reformat request by the rfc1123
    memcpy(outstr, days_names[tmp->tm_wday], 3);
    memcpy(outstr+8, month_names[tmp->tm_mon], 3);
    outstr[date_len]='\0';
    return outstr;
} 

char *cur_time_rfc1123()
{
    time_t t;
   
    time(&t);

    return time_rfc1123(t);
}

