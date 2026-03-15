#ifndef QUEUE_H
#define QUEUE_H

/*
 * Defines a Queue Data Structure
 * 
 * Fields:
 *     data (int*): The elements of the queue
 *     head (int): The index of the start of the queue
 *     tail (int): The index of the end of the queue
 */
struct Queue {
    int* data;
    int head;
    int tail;
};

/*
 * Add an element in the queue
 * 
 * Args: 
 *     q (struct Queue*): Pointer to the queue
 *     value (int): The value to append
 */
void enqueue(struct Queue* q, int val);

/*
 * Remove an element from the queue
 * 
 * Args: 
 *     q (struct Queue*): Pointer to the queue
 * 
 * Returns:
 *     value (int): The value that has been removed
 */
int dequeue(struct Queue* q);

/*
 * Check if the queue is empty
 * 
 * Args: 
 *     q (struct Queue*): Pointer to the queue
 * 
 * Returns:
 *     empty (int): Value that specifies if empty or not
 *     
 */
int is_empty(struct Queue* q);

#endif