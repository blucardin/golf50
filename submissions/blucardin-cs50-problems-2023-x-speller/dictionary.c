// Implements a dictionary's functionality

#include <ctype.h>
#include <stdbool.h>
#include <string.h>
#include <strings.h>
#include "dictionary.h"
#include <stdlib.h>
#include <stdio.h>

// Represents a node in a hash table
typedef struct node
{
    char word[LENGTH + 1];
    struct node *next;
}
node;

// TODO: Choose number of buckets in hash table
const unsigned int N = 226;

// Hash table
node *table[N];

// Returns true if word is in dictionary, else false
bool check(const char *word)
{
    int hashval = hash(word);
    for (node *tmp = table[hashval]; tmp != NULL; tmp = tmp -> next)
    {
        if (strcasecmp(tmp->word, word) == 0)
        {
            return true;
        }
    }
    return false;
}

// Hashes word to a number
unsigned int hash(const char *word)
{
    // TODO: Improve this hash function
    unsigned int sum = 0;
    for (int i = 0; word[i] != '\0'; i++)
    {
        int minihash = (toupper(word[i]) - 'A');
        if (minihash > 0)
        {
            sum += minihash;
        }

        if (i >= 9)
        {
            break;
        }
    }

    return sum;
}

// Loads dictionary into memory, returning true if successful, else false
bool load(const char *dictionary)
{
    FILE *input = fopen(dictionary, "r");
    if (input == NULL)
    {
        return false;
    }

    char word[LENGTH + 1];

    while (fscanf(input, "%s", word) != EOF)
    {
        node *n = malloc(sizeof(node));
        if (n == NULL)
        {
            return false;
        }
        strcpy(n->word, word);
        unsigned int hashval = hash(word);
        n->next = table[hashval];
        table[hashval] = n;
    }
    fclose(input);

    // TODO
    return true;
}

int count(node *current)
{
    if (current == NULL)
    {
        return 0;
    }
    else
    {
        return count(current->next) + 1;
    }
}

// Returns number of words in dictionary if loaded, else 0 if not yet loaded
unsigned int size(void)
{
    unsigned int total = 0;
    int CurCount;
    for (int i = 0; i < N; i++)
    {
        CurCount = count(table[i]);
        total += CurCount;
    }
    return total;
}


void recursion(node *current)
{
    if (current == NULL)
    {
        free(current); // maybe don't need this line
    }
    else
    {
        recursion(current->next);
        free(current);
    }
}

// Unloads dictionary from memory, returning true if successful, else false
bool unload(void)
{
    for (int i = 0; i < N; i++)
    {
        recursion(table[i]);
    }
    // TODO
    return true;
}

