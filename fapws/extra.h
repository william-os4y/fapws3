
void stripChar(char *s, char *d, char c) ;

char * decode_uri(const char *uri);

char * remove_leading_and_trailing_spaces(char* s);

int str_append3(char *dest, char *src1, char *src2, char *src3, int n);

char *cur_time(char * fmt);

char *time_rfc1123(time_t t);

char *cur_time_rfc1123(void);

