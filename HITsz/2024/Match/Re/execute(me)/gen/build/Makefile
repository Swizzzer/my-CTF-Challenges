TARGET = executeme
FLAG = flag.txt
ARCHIVE = executeme.tar.gz

.PHONY: all clean

all: $(FLAG) $(ARCHIVE)

$(FLAG): 
	python catflag.py

$(TARGET): 
	cargo zigbuild --target riscv64gc-unknown-linux-musl --release
	mv target/riscv64gc-unknown-linux-musl/release/executeme .

$(ARCHIVE): $(TARGET)
	tar czf $(ARCHIVE) $(TARGET)

clean:
	rm -f $(TARGET) $(ARCHIVE) $(FLAG)
