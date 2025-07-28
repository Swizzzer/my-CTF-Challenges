// filesystem.rs
use std::fs::{File, OpenOptions};
use std::io::{self, Read, Write, Seek, SeekFrom};
use flate2::Compression;
use flate2::write::DeflateEncoder;
use flate2::read::DeflateDecoder;

// 常量定义
const SECTOR_SIZE: usize = 512;
const CLUSTER_SIZE: usize = 4 * SECTOR_SIZE; // 2KB
const MAX_CLUSTERS: usize = 1024;  // 支持最多1024个簇
const FAT_ENTRIES_PER_SECTOR: usize = SECTOR_SIZE / 4; // 每个FAT项4字节
const FAT_SIZE_SECTORS: usize = (MAX_CLUSTERS + FAT_ENTRIES_PER_SECTOR - 1) / FAT_ENTRIES_PER_SECTOR;

// 文件系统布局
const BOOT_SECTOR_COUNT: usize = 1;
const FAT_START_SECTOR: usize = BOOT_SECTOR_COUNT;
const ROOT_DIR_START_SECTOR: usize = FAT_START_SECTOR + FAT_SIZE_SECTORS;
const ROOT_DIR_SECTORS: usize = 4;
const DATA_START_SECTOR: usize = ROOT_DIR_START_SECTOR + ROOT_DIR_SECTORS;
const DATA_SECTORS: usize = MAX_CLUSTERS * (CLUSTER_SIZE / SECTOR_SIZE);

// FAT特殊标记
const FAT_EOC: u32 = 0xFFFFFFFF;  // End of Chain
const FAT_FREE: u32 = 0x00000000; // 空闲簇
// const FAT_BAD: u32 = 0xFFFFFFFE;  // 坏簇

// 每个目录项的大小
const DIR_ENTRY_SIZE: usize = 64;
const MAX_FILENAME_LENGTH: usize = 32;

fn compress_data(data: &[u8]) -> io::Result<Vec<u8>> {
    let mut encoder = DeflateEncoder::new(Vec::new(), Compression::best());
    encoder.write_all(data)?;
    encoder.finish()
}

fn decompress_data(compressed_data: &[u8]) -> io::Result<Vec<u8>> {
    let mut decoder = DeflateDecoder::new(compressed_data);
    let mut decompressed = Vec::new();
    decoder.read_to_end(&mut decompressed)?;
    Ok(decompressed)
}
// FileEntry
#[derive(Debug, Clone)]
pub struct FileEntry {
    pub name: String,
    pub size: u32,
    pub compressed_size: u32,
    pub first_cluster: u32,
    pub is_deleted: bool,
    pub is_compressed: bool,
    pub compression_method: u8,  // 压缩方法: 0=无压缩, 1=RLE, 2=DEFLATE
}

impl FileEntry {
    fn new(name: &str, size: u32, compressed_size: u32, first_cluster: u32, compression_method: u8) -> Self {
        FileEntry {
            name: name.to_string(),
            size,
            compressed_size,
            first_cluster,
            is_deleted: false,
            is_compressed: compression_method > 0,
            compression_method,
        }
    }

    fn to_bytes(&self) -> [u8; DIR_ENTRY_SIZE] {
        let mut entry = [0u8; DIR_ENTRY_SIZE];
        
        // 写入文件名
        let name_bytes = self.name.as_bytes();
        let name_len = std::cmp::min(name_bytes.len(), MAX_FILENAME_LENGTH);
        entry[0..name_len].copy_from_slice(&name_bytes[0..name_len]);
        
        // 写入原始文件大小
        let size_bytes = self.size.to_le_bytes();
        entry[32..36].copy_from_slice(&size_bytes);
        
        // 写入压缩后大小
        let compressed_size_bytes = self.compressed_size.to_le_bytes();
        entry[36..40].copy_from_slice(&compressed_size_bytes);
        
        // 写入第一个簇号
        let cluster_bytes = self.first_cluster.to_le_bytes();
        entry[40..44].copy_from_slice(&cluster_bytes);
        
        // 写入删除标志
        entry[44] = if self.is_deleted { 1 } else { 0 };
        
        // 写入压缩标志
        entry[45] = if self.is_compressed { 1 } else { 0 };
        
        // 写入压缩方法
        entry[46] = self.compression_method;
        
        entry
    }

    fn from_bytes(bytes: &[u8]) -> Option<Self> {
        if bytes.len() < DIR_ENTRY_SIZE {
            return None;
        }
        
        // 查找文件名结束位置
        let mut name_end = 0;
        while name_end < MAX_FILENAME_LENGTH && bytes[name_end] != 0 {
            name_end += 1;
        }
        
        let name = String::from_utf8_lossy(&bytes[0..name_end]).to_string();
        let size = u32::from_le_bytes([bytes[32], bytes[33], bytes[34], bytes[35]]);
        let compressed_size = u32::from_le_bytes([bytes[36], bytes[37], bytes[38], bytes[39]]);
        let first_cluster = u32::from_le_bytes([bytes[40], bytes[41], bytes[42], bytes[43]]);
        let is_deleted = bytes[44] != 0;
        let is_compressed = bytes[45] != 0;
        let compression_method = bytes[46];
        
        Some(FileEntry {
            name,
            size,
            compressed_size,
            first_cluster,
            is_deleted,
            is_compressed,
            compression_method,
        })
    }
}

pub struct FileSystem {
    disk_image: File,
    path: String,
}

impl FileSystem {
    pub fn format(path: &str) -> io::Result<Self> {
        let total_size = (DATA_START_SECTOR + DATA_SECTORS) * SECTOR_SIZE;
        
        let file = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .truncate(true)
            .open(path)?;
            
        file.set_len(total_size as u64)?;
        let mut fs = FileSystem {
            disk_image: file,
            path: path.to_string(),
        };
        
        let mut boot_sector = vec![0u8; SECTOR_SIZE];
        boot_sector[0] = 0xEB; // Simulate x86 jump instruction
        boot_sector[1] = 0x3C;
        boot_sector[2] = 0x90;
        
        // Filesystem identifier "MINIFAT "
        let fs_name = b"MINIFAT ";
        boot_sector[3..11].copy_from_slice(fs_name);
        
        // Write sectors per cluster
        boot_sector[11] = (CLUSTER_SIZE / SECTOR_SIZE) as u8;
        
        // Write reserved sectors
        let reserved_sectors = BOOT_SECTOR_COUNT as u16;
        boot_sector[12..14].copy_from_slice(&reserved_sectors.to_le_bytes());
        
        // Write FAT count (1)
        boot_sector[14] = 1;
        
        // root directory entries
        let root_entries = ROOT_DIR_SECTORS * SECTOR_SIZE / DIR_ENTRY_SIZE;
        boot_sector[15..17].copy_from_slice(&(root_entries as u16).to_le_bytes());
    
        let total_sectors = (DATA_START_SECTOR + DATA_SECTORS) as u32;
        boot_sector[17..21].copy_from_slice(&total_sectors.to_le_bytes());
        
        boot_sector[21..23].copy_from_slice(&(FAT_SIZE_SECTORS as u16).to_le_bytes());
        
        // boot sector signature
        boot_sector[SECTOR_SIZE - 2] = 0x55;
        boot_sector[SECTOR_SIZE - 1] = 0xAA;
        
        // boot sector
        fs.disk_image.seek(SeekFrom::Start(0))?;
        fs.disk_image.write_all(&boot_sector)?;
        
        let mut fat_sector = vec![0u8; SECTOR_SIZE];
        fat_sector[0..4].copy_from_slice(&FAT_EOC.to_le_bytes());
        fat_sector[4..8].copy_from_slice(&FAT_EOC.to_le_bytes());
        
        fs.disk_image.seek(SeekFrom::Start((FAT_START_SECTOR * SECTOR_SIZE) as u64))?;
        fs.disk_image.write_all(&fat_sector)?;
        
        let zero_sector = vec![0u8; SECTOR_SIZE];
        for i in 1..FAT_SIZE_SECTORS {
            fs.disk_image.seek(SeekFrom::Start(((FAT_START_SECTOR + i) * SECTOR_SIZE) as u64))?;
            fs.disk_image.write_all(&zero_sector)?;
        }
        
        for i in 0..ROOT_DIR_SECTORS {
            fs.disk_image.seek(SeekFrom::Start(((ROOT_DIR_START_SECTOR + i) * SECTOR_SIZE) as u64))?;
            fs.disk_image.write_all(&zero_sector)?;
        }
        
        fs.disk_image.flush()?;
        
        Ok(fs)
    }
    
    // Mount existing file system
    pub fn mount(path: &str) -> io::Result<Self> {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .open(path)?;
            
        let mut boot_sector = [0u8; SECTOR_SIZE];
        let mut file_clone = file.try_clone()?; // Clone the file handle to avoid moving it
        file_clone.seek(SeekFrom::Start(0))?;
        file_clone.read_exact(&mut boot_sector)?;
        
        let fs_identifier = &boot_sector[3..11];
        if fs_identifier != b"MINIFAT " {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "不是有效的MINIFAT文件系统"));
        }
        
        if boot_sector[SECTOR_SIZE - 2] != 0x55 || boot_sector[SECTOR_SIZE - 1] != 0xAA {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "无效的启动扇区签名"));
        }
        
        Ok(FileSystem {
            disk_image: file,
            path: path.to_string(),
        })
    }
    
    pub fn get_or_create(path: &str) -> io::Result<Self> {
        match Self::mount(path) {
            Ok(fs) => Ok(fs),
            Err(_) => Self::format(path),
        }
    }
    fn get_next_cluster(&mut self, cluster: u32) -> io::Result<u32> {
        let fat_offset = FAT_START_SECTOR * SECTOR_SIZE + (cluster as usize * 4);
        self.disk_image.seek(SeekFrom::Start(fat_offset as u64))?;
        
        let mut next_cluster_bytes = [0u8; 4];
        self.disk_image.read_exact(&mut next_cluster_bytes)?;
        
        let next_cluster = u32::from_le_bytes(next_cluster_bytes);
        Ok(next_cluster)
    }
    
    fn set_next_cluster(&mut self, cluster: u32, next_cluster: u32) -> io::Result<()> {
        let fat_offset = FAT_START_SECTOR * SECTOR_SIZE + (cluster as usize * 4);
        self.disk_image.seek(SeekFrom::Start(fat_offset as u64))?;
        
        self.disk_image.write_all(&next_cluster.to_le_bytes())?;
        Ok(())
    }
    
    // 分配新簇
    fn allocate_cluster(&mut self) -> io::Result<u32> {
        // 从FAT表中查找空闲簇
        for cluster in 2..MAX_CLUSTERS as u32 {
            let next = self.get_next_cluster(cluster)?;
            if next == FAT_FREE {
                // 将此簇标记为文件结束
                self.set_next_cluster(cluster, FAT_EOC)?;
                return Ok(cluster);
            }
        }
        
        Err(io::Error::new(io::ErrorKind::Other, "磁盘空间不足，没有可用簇"))
    }
    
    // 释放簇链
    fn free_cluster_chain(&mut self, start_cluster: u32) -> io::Result<()> {
        if start_cluster < 2 {
            return Ok(());
        }
        
        let mut current = start_cluster;
        while current != FAT_EOC && current >= 2 {
            let next = self.get_next_cluster(current)?;
            self.set_next_cluster(current, FAT_FREE)?;
            current = next;
        }
        
        Ok(())
    }
    
    fn read_cluster(&mut self, cluster: u32) -> io::Result<Vec<u8>> {
        if cluster < 2 {
            return Err(io::Error::new(io::ErrorKind::InvalidInput, "无效的簇号"));
        }
        
        let cluster_offset = DATA_START_SECTOR * SECTOR_SIZE + (cluster as usize - 2) * CLUSTER_SIZE;
        self.disk_image.seek(SeekFrom::Start(cluster_offset as u64))?;
        
        let mut cluster_data = vec![0u8; CLUSTER_SIZE];
        self.disk_image.read_exact(&mut cluster_data)?;
        
        Ok(cluster_data)
    }
    
    // 写入一个簇的数据
    fn write_cluster(&mut self, cluster: u32, data: &[u8]) -> io::Result<()> {
        if cluster < 2 {
            return Err(io::Error::new(io::ErrorKind::InvalidInput, "无效的簇号"));
        }
        
        if data.len() > CLUSTER_SIZE {
            return Err(io::Error::new(io::ErrorKind::InvalidInput, "数据大于簇大小"));
        }
        
        let cluster_offset = DATA_START_SECTOR * SECTOR_SIZE + (cluster as usize - 2) * CLUSTER_SIZE;
        self.disk_image.seek(SeekFrom::Start(cluster_offset as u64))?;
        
        let mut cluster_data = vec![0u8; CLUSTER_SIZE];
        cluster_data[0..data.len()].copy_from_slice(data);
        
        self.disk_image.write_all(&cluster_data)?;
        
        Ok(())
    }
    
    fn read_directory_entries(&mut self) -> io::Result<Vec<FileEntry>> {
        let root_dir_size = ROOT_DIR_SECTORS * SECTOR_SIZE;
        let mut root_dir_data = vec![0u8; root_dir_size];
        
        self.disk_image.seek(SeekFrom::Start((ROOT_DIR_START_SECTOR * SECTOR_SIZE) as u64))?;
        self.disk_image.read_exact(&mut root_dir_data)?;
        
        let mut entries = Vec::new();
        let entry_count = root_dir_size / DIR_ENTRY_SIZE;
        
        for i in 0..entry_count {
            let offset = i * DIR_ENTRY_SIZE;
            let entry_data = &root_dir_data[offset..offset + DIR_ENTRY_SIZE];
            
            // 检查是否是有效的文件项
            if entry_data[0] != 0 {
                if let Some(entry) = FileEntry::from_bytes(entry_data) {
                    if !entry.is_deleted {
                        entries.push(entry);
                    }
                }
            }
        }
        
        Ok(entries)
    }
    
    fn write_directory_entry(&mut self, entry: &FileEntry) -> io::Result<()> {
        let root_dir_size = ROOT_DIR_SECTORS * SECTOR_SIZE;
        let mut root_dir_data = vec![0u8; root_dir_size];
        
        self.disk_image.seek(SeekFrom::Start((ROOT_DIR_START_SECTOR * SECTOR_SIZE) as u64))?;
        self.disk_image.read_exact(&mut root_dir_data)?;
        
        let entry_count = root_dir_size / DIR_ENTRY_SIZE;
        let entry_bytes = entry.to_bytes();
        
        for i in 0..entry_count {
            let offset = i * DIR_ENTRY_SIZE;
            
            if root_dir_data[offset] == 0 || {
                if let Some(existing) = FileEntry::from_bytes(&root_dir_data[offset..offset + DIR_ENTRY_SIZE]) {
                    existing.name == entry.name || existing.is_deleted
                } else {
                    false
                }
            } {
                root_dir_data[offset..offset + DIR_ENTRY_SIZE].copy_from_slice(&entry_bytes);
                
                // 写回根目录区
                self.disk_image.seek(SeekFrom::Start((ROOT_DIR_START_SECTOR * SECTOR_SIZE) as u64))?;
                self.disk_image.write_all(&root_dir_data)?;
                
                return Ok(());
            }
        }
        
        Err(io::Error::new(io::ErrorKind::Other, "根目录已满，无法创建更多文件"))
    }
    
    fn find_file(&mut self, filename: &str) -> io::Result<Option<FileEntry>> {
        let entries = self.read_directory_entries()?;
        
        for entry in entries {
            if entry.name == filename && !entry.is_deleted {
                return Ok(Some(entry));
            }
        }
        
        Ok(None)
    }
    
    pub fn write_file(&mut self, filename: &str, data: &[u8], compression_method: Option<u8>) -> io::Result<()> {
        let compression_method = compression_method.unwrap_or(2); // 默认使用DEFLATE(2)
        
        let (compressed_data, original_size, compressed_size) = match compression_method {
            0 => {
                // 不压缩
                (data.to_vec(), data.len(), data.len())
            },
            1 => {
                // RLE压缩
                let compressed = rle_compress_data(data);
                (compressed.clone(), data.len(), compressed.len())
            },
            2 => {
                // DEFLATE压缩
                let compressed = compress_data(data)?;
                (compressed.clone(), data.len(), compressed.len())
            },
            _ => return Err(io::Error::new(io::ErrorKind::InvalidInput, "不支持的压缩方法"))
        };
        
        // 存在同名文件则删除
        if let Ok(Some(_)) = self.find_file(filename) {
            self.delete_file(filename)?;
        }
        
        let clusters_needed = (compressed_size + CLUSTER_SIZE - 1) / CLUSTER_SIZE;
        
        // 空文件至少分配一个簇
        let clusters_needed = std::cmp::max(clusters_needed, 1);
        
        let first_cluster = self.allocate_cluster()?;
        let mut current_cluster = first_cluster;
        
        // 按块写入压缩数据
        for chunk_index in 0..clusters_needed {
            let start = chunk_index * CLUSTER_SIZE;
            let end = std::cmp::min(start + CLUSTER_SIZE, compressed_size);
            
            if start < compressed_size {
                let chunk = if start < compressed_data.len() {
                    if end <= compressed_data.len() {
                        &compressed_data[start..end]
                    } else {
                        &compressed_data[start..compressed_data.len()]
                    }
                } else {
                    &[]
                };
                
                self.write_cluster(current_cluster, chunk)?;
                
                if chunk_index < clusters_needed - 1 {
                    let next_cluster = self.allocate_cluster()?;
                    self.set_next_cluster(current_cluster, next_cluster)?;
                    current_cluster = next_cluster;
                }
            }
        }
        
        // 标记文件结尾
        self.set_next_cluster(current_cluster, FAT_EOC)?;
        
        let entry = FileEntry::new(
            filename, 
            original_size as u32, 
            compressed_size as u32, 
            first_cluster,
            compression_method
        );
        
        self.write_directory_entry(&entry)?;
        
        Ok(())
    }
    
    pub fn read_file(&mut self, filename: &str) -> io::Result<Vec<u8>> {
        let file_entry = match self.find_file(filename)? {
            Some(entry) => entry,
            None => return Err(io::Error::new(io::ErrorKind::NotFound, "文件不存在")),
        };
        
        let mut compressed_data = Vec::new();
        let mut current_cluster = file_entry.first_cluster;
        
        while current_cluster != FAT_EOC && current_cluster >= 2 {
            let cluster_data = self.read_cluster(current_cluster)?;
            
            let remaining = file_entry.compressed_size as usize - compressed_data.len();
            let to_read = std::cmp::min(remaining, cluster_data.len());
            
            if to_read > 0 {
                compressed_data.extend_from_slice(&cluster_data[0..to_read]);
            }
            
            if compressed_data.len() >= file_entry.compressed_size as usize {
                break;
            }
            
            current_cluster = self.get_next_cluster(current_cluster)?;
        }
        
        if file_entry.is_compressed {
            match file_entry.compression_method {
                0 => {
                    Ok(compressed_data)
                },
                1 => {
                    // RLE解压
                    let decompressed = rle_decompress_data(&compressed_data);
                    
                    if decompressed.len() != file_entry.size as usize {
                        return Err(io::Error::new(io::ErrorKind::InvalidData, 
                            format!("RLE解压错误：解压后大小({})与预期大小({})不匹配", 
                                decompressed.len(), file_entry.size)));
                    }
                    
                    Ok(decompressed)
                },
                2 => {
                    // DEFLATE解压
                    let decompressed = decompress_data(&compressed_data)?;
                    
                    if decompressed.len() != file_entry.size as usize {
                        return Err(io::Error::new(io::ErrorKind::InvalidData, 
                            format!("DEFLATE解压错误：解压后大小({})与预期大小({})不匹配", 
                                decompressed.len(), file_entry.size)));
                    }
                    
                    Ok(decompressed)
                },
                _ => Err(io::Error::new(io::ErrorKind::InvalidData, "不支持的压缩方法")),
            }
        } else {
            Ok(compressed_data)
        }
    }
    pub fn write_file_with_compression(&mut self, filename: &str, data: &[u8], compression_method: u8) -> io::Result<()> {
        self.write_file(filename, data, Some(compression_method))
    }
    pub fn get_compression_stats(&mut self, filename: &str) -> io::Result<(u32, u32, f32, &str)> {
        let file_entry = match self.find_file(filename)? {
            Some(entry) => entry,
            None => return Err(io::Error::new(io::ErrorKind::NotFound, "文件不存在")),
        };
        
        let compression_name = match file_entry.compression_method {
            0 => "无压缩",
            1 => "RLE压缩",
            2 => "DEFLATE压缩",
            _ => "未知压缩方法",
        };
        
        let ratio = if file_entry.size > 0 {
            (file_entry.compressed_size as f32 / file_entry.size as f32) * 100.0
        } else {
            0.0
        };
        
        Ok((file_entry.size, file_entry.compressed_size, ratio, compression_name))
    }
    pub fn list_files(&mut self) -> io::Result<Vec<FileEntry>> {
        self.read_directory_entries()
    }
    
    pub fn delete_file(&mut self, filename: &str) -> io::Result<()> {
        let file_entry = match self.find_file(filename)? {
            Some(entry) => entry,
            None => return Err(io::Error::new(io::ErrorKind::NotFound, "文件不存在")),
        };
        
        self.free_cluster_chain(file_entry.first_cluster)?;
        
        let mut entry = file_entry.clone();
        entry.is_deleted = true;
        self.write_directory_entry(&entry)?;
        
        Ok(())
    }
}

fn rle_compress_data(data: &[u8]) -> Vec<u8> {
    if data.is_empty() {
        return Vec::new();
    }

    let mut result = Vec::new();
    let mut current_byte = data[0];
    let mut count: u8 = 1;

    for &byte in data.iter().skip(1) {
        if byte == current_byte && count < 255 {
            count += 1;
        } else {
            result.push(count);
            result.push(current_byte);
            
            current_byte = byte;
            count = 1;
        }
    }

    result.push(count);
    result.push(current_byte);

    result
}

fn rle_decompress_data(compressed_data: &[u8]) -> Vec<u8> {
    if compressed_data.is_empty() {
        return Vec::new();
    }

    let mut result = Vec::new();
    let mut i = 0;

    while i < compressed_data.len() {
        if i + 1 >= compressed_data.len() {
            break;
        }

        let count = compressed_data[i] as usize;
        let byte = compressed_data[i + 1];

        for _ in 0..count {
            result.push(byte);
        }

        i += 2;
    }

    result
}