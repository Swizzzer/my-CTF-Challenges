use std::io::{self};

mod encoder;

fn main() {
    println!("Enter your flag:");
    let mut input_string = String::new();
    io::stdin()
        .read_line(&mut input_string)
        .expect("Failed to read line");

    input_string = input_string.trim_end().to_owned();

    let input_numbers = input_string.bytes().map(|b| b as i32).collect::<Vec<i32>>();

    let mut encoded_bytes = Vec::new();
    encoder::encode(&mut encoded_bytes, &input_numbers);

    let encoded_string = String::from_utf8(encoded_bytes).unwrap();

    let correct = "FLAG_TEMPLATE".to_string();
    if encoded_string == correct {
        println!("Correct flag!");
    } else {
        println!("Incorrect flag.");
    }
}
