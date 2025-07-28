require 'sinatra'
require 'json'
set :bind, '0.0.0.0'

flag = open('flag.txt').read.strip

helpers do
  def win_patterns
    [
      [0, 1, 2], [3, 4, 5], [6, 7, 8], # 行
      [0, 3, 6], [1, 4, 7], [2, 5, 8], # 列
      [0, 4, 8], [2, 4, 6]             # 对角线
    ]
  end

  def game_over?(board)
    !check_winner(board).nil?
  end

  def check_winner(board)
    win_patterns.each do |pattern|
      current = board[pattern[0]]
      next unless current && current == board[pattern[1]] && current == board[pattern[2]]
      return current
    end
    nil
  end

  def board_full?(board)
    board.none?(nil)
  end

  def minimax(board, depth, is_maximizing, alpha = -Float::INFINITY, beta = Float::INFINITY)
    case check_winner(board)
    when 'O' then return 10 - depth
    when 'X' then return depth - 10
    end

    return 0 if board_full?(board)

    if is_maximizing
      maximize_score(board, depth, alpha, beta)
    else
      minimize_score(board, depth, alpha, beta)
    end
  end

  def maximize_score(board, depth, alpha, beta)
    best = -Float::INFINITY
    each_valid_move(board) do |i|
      board[i] = 'O'
      score = minimax(board, depth + 1, false, alpha, beta)
      board[i] = nil
      best = [best, score].max
      alpha = [alpha, best].max
      break if beta <= alpha
    end
    best
  end

  def minimize_score(board, depth, alpha, beta)
    best = Float::INFINITY
    each_valid_move(board) do |i|
      board[i] = 'X'
      score = minimax(board, depth + 1, true, alpha, beta)
      board[i] = nil
      best = [best, score].min
      beta = [beta, best].min
      break if beta <= alpha
    end
    best
  end

  def each_valid_move(board, &block)
    9.times { |i| yield i if board[i].nil? }
  end

  def ai_move(board)
    best_score = -Float::INFINITY
    best_move = nil

    each_valid_move(board) do |i|
      board[i] = 'O'
      score = minimax(board, 0, false)
      board[i] = nil
      if score > best_score
        best_score = score
        best_move = i
      end
    end

    best_move
  end
end

get '/' do
  erb :index
end

post '/move' do
  content_type :json
  data = JSON.parse(request.body.read)
  board = data['board']
  user_pos = data['position'].to_i

  board[user_pos] = 'X'

  return { status: 'win', flag: flag, board: board }.to_json if game_over?(board)
  return { status: 'draw', board: board }.to_json if board_full?(board)

  ai_pos = ai_move(board)
  board[ai_pos] = 'O'

  if game_over?(board)
    { status: 'lose', message: 'Not so powerful...', board: board }.to_json
  else
    board_full?(board) ? { status: 'draw', board: board }.to_json : { status: 'continue', board: board }.to_json
  end
end