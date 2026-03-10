#include <stdlib.h>
#include "../include/queue.h"

void enqueue(struct Queue* q, int val){
    q->data[q->tail++] = val;
}

int dequeue(struct Queue* q){
    return q->data[q->head++];
}

int is_empty(struct Queue* q){
    return q->head == q->tail;
}