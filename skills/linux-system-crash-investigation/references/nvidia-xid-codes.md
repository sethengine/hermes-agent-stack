# NVIDIA Xid Error Codes

Xid errors are GPU hardware faults reported by the NVIDIA kernel driver.
Look for them with: `dmesg | grep 'NVRM: Xid'` or `journalctl -b 0 -k | grep Xid`

## Common Xid Codes

| Xid | Meaning | Typical Cause |
|-----|---------|---------------|
| 13 | Graphics Engine Exception | Shader error, bad draw call |
| 31 | **MMU Fault** | GPU page table fault — invalid DMA buffer mapping. Often NVDEC0 (video decoder) triggered by VA-API bridge bugs. |
| 45 | Preemptive Channel Removal | Driver forcibly killed a GPU channel (often after timeout) |
| 48 | Double Bit ECC Error | Uncorrectable VRAM error (rare on consumer GPUs) |
| 69 | Internal Video Memory Controller Error | VRAM controller issue |
| 79 | **GPU has fallen off the bus** | PCIe link failure — GPU disconnected from system. Power delivery, riser cable, PCIe signal integrity. |
| 92 | High single-bit ECC error threshold | Correctable VRAM errors exceeding threshold |
| 109 | ChCont Recoverable fatal error | Context switch failure during recovery |
| 119 | GPU Recovery Action Required | GPU needs to be reset to recover |
| 140 | GPU Critical Error | Catastrophic GPU failure |

## Xid 31 Deep Dive (RTX 5060 Ti + libva-nvidia-driver)

Observed pattern on this system:
```
NVRM: Xid (PCI:0000:02:00): 31, pid=..., name=chrome, channel 0x09000001
  MMU Fault: ENGINE NVDEC0 HUBCLIENT_NVDEC0 faulted @ 0x1_05f6d000
  Fault is of type FAULT_PDE ACCESS_TYPE_VIRT_WRITE
```

- **ENGINE NVDEC0**: Hardware video decoder engine
- **FAULT_PDE**: Page directory entry fault — invalid/incomplete GPU page table
- **ACCESS_TYPE_VIRT_WRITE**: GPU tried to DMA-write to a buffer whose mapping was torn down

**Root cause**: libva-nvidia-driver + Chrome `VaapiIgnoreDriverChecks` flag using the experimental VA-API → NVDEC bridge. The driver doesn't properly manage GPU virtual address space for NVDEC DMA buffers on RTX 5060 Ti (PCI 0x2d04).

**Accumulation risk**: Multiple Xid 31 errors can corrupt the GPU's virtual address space:
```
nvAssertFailedNoLog: Assertion failed: vaHi <= pMemBlock->end @ gpu_vaspace.c:2022
dmaAllocMapping_GM107: can't update VA space for mapping
```
After enough corruption, the GPU hangs → system lockup → forced reset.

**Fix**:
1. Disable Chrome GPU video decode: `chrome://flags/#disable-accelerated-video-decode`
2. Or remove `VaapiIgnoreDriverChecks` from Chrome startup flags
3. Or try `nvidia_vulkan_drv_video.so` (Vulkan Video backend) instead of NVDEC direct
