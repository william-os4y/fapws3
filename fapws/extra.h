#ifndef FAPWS3_EXTRA_H
#define FAPWS3_EXTRA_H

#include <syslog.h> //loglevel: LOG_*

void stripChar(char *s, char *d, char c) ;

char * decode_uri(const char *uri);

char * remove_leading_and_trailing_spaces(char* s);

int str_append3(char *dest, char *src1, char *src2, char *src3, int n);

char *cur_time(char * fmt);

char *time_rfc1123(time_t t);

char *cur_time_rfc1123(void);

void log_debug(unsigned int priority, const char* file, const char* func, int line, const char* fmt, ...) __attribute__((format (printf, 5, 6)));

#define LERROR(fmt, ...) do { log_debug(LOG_ERR,   __FILE__, __FUNCTION__, __LINE__, fmt, ## __VA_ARGS__); } while(0)
#define LDEBUG(fmt, ...) do { if (debug) log_debug(LOG_DEBUG, __FILE__, __FUNCTION__, __LINE__, fmt, ## __VA_ARGS__); } while(0)

#endif //FAPWS3_EXTRA_H
