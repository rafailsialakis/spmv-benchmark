#ifndef QUEUE_H
#define QUEUE_H

struct Queue {
    int* data;
    int head;
    int tail;
};

void enqueue(struct Queue* q, int val);
int dequeue(struct Queue* q);
int is_empty(struct Queue* q);

#endif