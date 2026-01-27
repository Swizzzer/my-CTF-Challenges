# compile with "https://github.com/za233/Polaris-Obfuscator" 
CXX := ./clang++
CXXFLAGS := -std=c++17 -mllvm -passes=indcall,alias,indbr,bcf,sub,mba,fla
LDFLAGS := -static 

BUILD_DIR := build

TARGET := $(BUILD_DIR)/camellia

SRCS := main.cpp camellia.cpp
OBJS := $(patsubst %.cpp,$(BUILD_DIR)/%.o,$(SRCS))
DEPS := $(patsubst %.cpp,$(BUILD_DIR)/%.d,$(SRCS))

.PHONY: all
all: $(TARGET)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(TARGET): $(OBJS) | $(BUILD_DIR)
	$(CXX) $(LDFLAGS) -o $@ $^

$(BUILD_DIR)/%.o: %.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c -o $@ $<

-include $(DEPS)

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)

.PHONY: run
run: $(TARGET)
	$(TARGET)

