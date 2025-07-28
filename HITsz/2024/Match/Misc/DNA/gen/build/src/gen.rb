require "doublehelix"

dna = doublehelix('puts"FLAG_TEMPLATE"')


def replace_randomly_on_random_lines(dna_string)
  dna_string.each_line.map do |line|
    if rand < 0.8 

      chars = %w[A G C T]
      indexes = line.chars.each_with_index.select { |char, _| chars.include?(char) }
      
      unless indexes.empty?
        _, index_to_replace = indexes.sample
        line[index_to_replace] = ' '
      end
    end
    line
  end.join
end

modified_dna = replace_randomly_on_random_lines(dna)
puts modified_dna
