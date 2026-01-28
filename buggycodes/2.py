def is_palindrome(s):
    rev = ""
    for i in range(len(s)):
        rev += s[len(s)-1-i]
    if rev == s:
        return True
