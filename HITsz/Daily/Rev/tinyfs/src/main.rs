// main.rs
use std::io::{self, Write};
use std::process;

mod filesystem;
use filesystem::FileSystem;

fn main() {
    println!("1. 创建/格式化磁盘镜像");
    println!("2. 写入文件（默认压缩方式）");
    println!("3. 写入文件（自定义压缩方式）");
    println!("4. 读取文件");
    println!("5. 列出文件");
    println!("6. 删除文件");
    println!("7. 查看文件压缩统计");
    println!("8. 退出");

    let mut disk_image_path = String::new();
    let mut fs: Option<FileSystem> = None;

    loop {
        print!("请选择操作 (1-8): ");
        io::stdout().flush().unwrap();

        let mut choice = String::new();
        io::stdin().read_line(&mut choice).expect("读取输入失败");

        match choice.trim() {
            "1" => {
                print!("请输入磁盘镜像文件路径: ");
                io::stdout().flush().unwrap();
                
                disk_image_path.clear();
                io::stdin().read_line(&mut disk_image_path).expect("读取输入失败");
                disk_image_path = disk_image_path.trim().to_string();
                
                match FileSystem::get_or_create(&disk_image_path) {
                    Ok(filesystem) => {
                        println!("磁盘镜像格式化成功: {}", disk_image_path);
                        fs = Some(filesystem);
                    }
                    Err(e) => println!("格式化磁盘镜像失败: {}", e),
                }
            }
            "2" => {
                if fs.is_none() {
                    println!("请先创建或挂载磁盘镜像");
                    continue;
                }

                print!("请输入文件名: ");
                io::stdout().flush().unwrap();
                let mut filename = String::new();
                io::stdin().read_line(&mut filename).expect("读取输入失败");
                filename = filename.trim().to_string();

                print!("请输入要写入的数据: ");
                io::stdout().flush().unwrap();
                let mut data = String::new();
                io::stdin().read_line(&mut data).expect("读取输入失败");
                
                match fs.as_mut().unwrap().write_file(&filename, data.as_bytes(), Some(2)) {
                    Ok(_) => println!("文件写入成功（使用DEFLATE压缩）"),
                    Err(e) => println!("文件写入失败: {}", e),
                }
            }
            "3" => {
                if fs.is_none() {
                    println!("请先创建或挂载磁盘镜像");
                    continue;
                }

                print!("请输入文件名: ");
                io::stdout().flush().unwrap();
                let mut filename = String::new();
                io::stdin().read_line(&mut filename).expect("读取输入失败");
                filename = filename.trim().to_string();

                print!("请输入要写入的数据: ");
                io::stdout().flush().unwrap();
                let mut data = String::new();
                io::stdin().read_line(&mut data).expect("读取输入失败");
                
                println!("请选择压缩方式:");
                println!("0 - 不压缩");
                println!("1 - RLE压缩");
                println!("2 - DEFLATE压缩");
                print!("选择 (0-2): ");
                io::stdout().flush().unwrap();
                
                let mut compression_choice = String::new();
                io::stdin().read_line(&mut compression_choice).expect("读取输入失败");
                let compression_method = compression_choice.trim().parse::<u8>().unwrap_or(2);
                
                match fs.as_mut().unwrap().write_file_with_compression(&filename, data.as_bytes(), compression_method) {
                    Ok(_) => {
                        let method_name = match compression_method {
                            0 => "不压缩",
                            1 => "RLE压缩",
                            2 => "DEFLATE压缩",
                            _ => "未知压缩方式",
                        };
                        println!("文件写入成功（使用{}）", method_name);
                    },
                    Err(e) => println!("文件写入失败: {}", e),
                }
            }
            "4" => {
                if fs.is_none() {
                    println!("请先创建或挂载磁盘镜像");
                    continue;
                }

                print!("请输入要读取的文件名: ");
                io::stdout().flush().unwrap();
                let mut filename = String::new();
                io::stdin().read_line(&mut filename).expect("读取输入失败");
                filename = filename.trim().to_string();
                
                match fs.as_mut().unwrap().read_file(&filename) {
                    Ok(data) => {
                        let content = String::from_utf8_lossy(&data);
                        println!("文件内容: {}", content);
                    }
                    Err(e) => println!("读取文件失败: {}", e),
                }
            }
            "5" => {
                if fs.is_none() {
                    println!("请先创建或挂载磁盘镜像");
                    continue;
                }

                match fs.as_mut().unwrap().list_files() {
                    Ok(files) => {
                        if files.is_empty() {
                            println!("磁盘镜像中没有文件");
                        } else {
                            println!("文件列表:");
                            for file in files {
                                let compression_method = match file.compression_method {
                                    0 => "无压缩",
                                    1 => "RLE",
                                    2 => "DEFLATE",
                                    _ => "未知",
                                };
                                println!("  {} (原始大小: {} 字节, 压缩后: {} 字节, 方式: {})",
                                    file.name, file.size, file.compressed_size, compression_method);
                            }
                        }
                    }
                    Err(e) => println!("列出文件失败: {}", e),
                }
            }
            "6" => {
                if fs.is_none() {
                    println!("请先创建或挂载磁盘镜像");
                    continue;
                }

                print!("请输入要删除的文件名: ");
                io::stdout().flush().unwrap();
                let mut filename = String::new();
                io::stdin().read_line(&mut filename).expect("读取输入失败");
                filename = filename.trim().to_string();
                
                match fs.as_mut().unwrap().delete_file(&filename) {
                    Ok(_) => println!("文件删除成功"),
                    Err(e) => println!("删除文件失败: {}", e),
                }
            }
            "7" => {
                if fs.is_none() {
                    println!("请先创建或挂载磁盘镜像");
                    continue;
                }

                print!("请输入要查看压缩统计的文件名: ");
                io::stdout().flush().unwrap();
                let mut filename = String::new();
                io::stdin().read_line(&mut filename).expect("读取输入失败");
                filename = filename.trim().to_string();
                
                match fs.as_mut().unwrap().get_compression_stats(&filename) {
                    Ok((original_size, compressed_size, ratio, method_name)) => {
                        println!("文件: {}", filename);
                        println!("压缩方式: {}", method_name);
                        println!("原始大小: {} 字节", original_size);
                        println!("压缩后大小: {} 字节", compressed_size);
                        println!("压缩率: {:.2}%", ratio);
                        println!("节省空间: {:.2}%", 100.0 - ratio);
                    }
                    Err(e) => println!("获取压缩统计失败: {}", e),
                }
            }
            "8" => {
                println!("退出程序");
                process::exit(0);
            }
            _ => println!("无效的选择，请重新输入"),
        }
    }
}

