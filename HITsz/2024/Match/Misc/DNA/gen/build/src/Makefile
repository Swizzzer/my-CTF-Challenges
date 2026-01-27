TARGET = DNA.txt
FLAG = flag.txt
ARCHIVE = DNA.tar.gz

.PHONY: all clean

all: $(FLAG) $(ARCHIVE)

$(FLAG): 
	python catflag.py

$(TARGET): 
	ruby gen.rb > $(TARGET)

$(ARCHIVE): $(TARGET)
	tar czf $(ARCHIVE) $(TARGET)

clean:
	rm -f $(TARGET) $(ARCHIVE) $(FLAG)
