
int setnonblock(int fd);

void close_connection(struct client *cli);

void timer_cb(struct ev_loop *loop, ev_timer *w, int revents);

void idle_cb(struct ev_loop *loop, ev_idle *w, int revents);

int handle_uri(struct client *cli);

int python_handler(struct client *cli);

int write_cli(struct client *cli, char *response, size_t len,  int revents);

void write_cb(struct ev_loop *loop, struct ev_io *w, int revents);

void connection_cb(struct ev_loop *loop, struct ev_io *w, int revents);

void accept_cb(struct ev_loop *loop, struct ev_io *w, int revents);

void sigint_cb(struct ev_loop *loop, ev_signal *w, int revents);

void sigterm_cb(struct ev_loop *loop, ev_signal *w, int revents);

void sigpipe_cb(struct ev_loop *loop, ev_signal *w, int revents);
