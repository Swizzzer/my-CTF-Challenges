const ALPHABET: [u8; 58] = *b"982647513ABCDEJHGFKLMNPQRSTUVWZXYabcdefghijkmnopqrstuv!@#$";

pub fn encode(out: &mut Vec<u8>, input: &Vec<i32>) {
    input.clone().iter_mut().for_each(|in_byte| {
        out.iter_mut().for_each(|out_byte| {
            *in_byte += (*out_byte as i32) << 8; // move over one sig digit
            *out_byte = (*in_byte % 58) as u8;
            *in_byte /= 58;
        });

        while *in_byte > 0 {
            out.push((*in_byte % 58) as u8);
            *in_byte /= 58;
        }
    });

    input
        .iter() // highest sig digits will get filtered out by > 0 check, add back
        .take_while(|c| **c == 0)
        .for_each(|_| out.push(0));

    out.iter_mut().for_each(|c| *c = ALPHABET[*c as usize]);
}
