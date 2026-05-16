MCU  = stm8s003f3
ARCH = stm8

F_CPU   ?= 2000000
TARGET  ?= main

BUILD_DIR= build

DEFINE   =
INCLUDE  =

SRCS    := $(wildcard *.c)
ASRCS   := $(wildcard *.s)

CC       = sdcc
LD       = sdld
AS       = sdasstm8
OBJCOPY  = sdobjcopy
ASFLAGS  = -plosgff
CFLAGS   = -m$(ARCH) -p$(MCU) --std-sdcc11
CFLAGS  += -DF_CPU=$(F_CPU)UL -I. $(INCLUDE) $(DEFINE)
CFLAGS  += --stack-auto --noinduction --use-non-free
LDFLAGS  = -m$(ARCH) -l$(ARCH) --out-fmt-ihx

OBJS     = $(addprefix $(BUILD_DIR)/,$(notdir $(SRCS:.c=.rel)))
OBJS    += $(addprefix $(BUILD_DIR)/,$(notdir $(ASRCS:.s=.rel)))
vpath %.c  $(sort $(dir $(SRCS)))
vpath %.s  $(sort $(dir $(ASRCS)))

all: $(BUILD_DIR)/$(TARGET).bin size

$(BUILD_DIR)/%.rel: %.c | $(BUILD_DIR)
	$(CC) -c $(CFLAGS) $< -o $@

$(BUILD_DIR)/%.rel: %.s | $(BUILD_DIR)
	$(AS) $(ASFLAGS) $<
	mv *.lst *.rel *.sym $(BUILD_DIR)

$(BUILD_DIR)/$(TARGET).hex: $(OBJS)
	$(CC) $(LDFLAGS) $(OBJS) -o $@

$(BUILD_DIR)/$(TARGET).bin: $(BUILD_DIR)/$(TARGET).hex
	$(OBJCOPY) -I ihex --output-target=binary $(BUILD_DIR)/$(TARGET).hex $(BUILD_DIR)/$(TARGET).bin

size: $(BUILD_DIR)/$(TARGET).bin
	@echo "Image size:"
	@stat -L -c %s $(BUILD_DIR)/$(TARGET).bin

$(BUILD_DIR):
	mkdir $@

clean:
	rm -fR $(BUILD_DIR)

flash: $(BUILD_DIR)/$(TARGET).hex
	stm8flash -c stlinkv2 -p $(MCU) -w $(BUILD_DIR)/$(TARGET).hex

lock:
	@echo '0xaa 0x00 0xff 0x00 0xff 0x00 0xff 0x00 0xff 0x00 0xff' | xxd -r > opt.bin
	stm8flash -c stlinkv2 -p $(MCU) -s opt -w opt.bin
	rm opt.bin

unlock:
	@echo '0x00 0x00 0xff 0x00 0xff 0x00 0xff 0x00 0xff 0x00 0xff' | xxd -r > opt.bin
	stm8flash -c stlinkv2 -p $(MCU) -s opt -w opt.bin
	rm opt.bin

serial: $(BUILD_DIR)/$(TARGET).hex
	stm8gal -p /dev/ttyUSB0 -w $(BUILD_DIR)/$(TARGET).hex

.PHONY: clean all flash
