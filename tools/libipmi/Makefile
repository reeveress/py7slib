OBJ=ipmi.o
OUT=libipmi.a
OUT_SO=libipmi.so

CC=$(CROSS_COMPILE)gcc

CFLAGS+=-fPIC -shared -Wall -Wextra -ggdb

all: $(OUT) $(OUT_SO)

$(OUT): $(OBJ)
	ar rcs $(OUT) $(OBJ)

$(OUT_SO): $(OBJ)
	$(CC) $< $(CFLAGS) -shared -fPIC -L. -Wl,-soname,$@ -o $@

clean:
	rm -rf $(OBJ) $(OUT) $(OUT_SO)

install:
	@echo "No install for $(OUT_SO)"
