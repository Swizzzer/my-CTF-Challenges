use hex;
use md5;
use std::io::{self, Write};
use std::process::exit;

fn main() {
    let strings = [
        "Hello, world!",
        "Patch it",
        "MD5 hashing",
        "Cryptography",
        "Computer Science",
        "Algorithm",
        "Data Structure",
        "Security",
    ];

    print!("🔑 ");
    io::stdout().flush().unwrap();

    let mut input = String::new();
    io::stdin().read_line(&mut input).expect("❌ ");
    let input = input.trim();
    if input.len() > 16 {
        println!("Stage 1 ❌ \n");
        exit(1);
    }
    if input.len() < 16 {
        println!("Stage 2 ❌ \n");
        exit(1);
    }
    let mut result = String::new();

    for s in &strings {
        let hash = md5::compute(s.as_bytes());
        let hex_str = hex::encode(&hash[0..2]).to_lowercase();
        result.push_str(&hex_str);
    }

    println!("🚩 HITCTF{{{}}}", result);
}
