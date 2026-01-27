CC = gcc 
CFLAGS = -Wall 
TARGET = segTree
GENERATE_FLAG_SRC = gen.c
MAIN_SRC = chall.c
FLAG_HEADER = flag.h


all: $(TARGET)

$(FLAG_HEADER): $(GENERATE_FLAG_SRC)
	$(CC) $(CFLAGS) -o gen $(GENERATE_FLAG_SRC) 
	./gen > $(FLAG_HEADER)
	rm -f gen


$(TARGET): $(MAIN_SRC) $(FLAG_HEADER)
	$(CC) $(CFLAGS) -o $(TARGET) $(MAIN_SRC) 

clean:
	rm -f $(TARGET) $(FLAG_HEADER) gen
