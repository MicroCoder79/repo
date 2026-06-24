import sys

print("Python Interactive Console")
print("Type 'exit' to close, 'clear' to reset variables.\n")

globals_dict = {}

while True:
	try:
		code = input(">>> ")
		
		if code.strip() == "exit":
			break
		elif code.strip() == "clear":
			globals_dict.clear()
			print("Console cleared.")
			continue
			
		if code.strip():
			if not code.startswith("print") and "=" not in code:
				try:
					result = eval(code, globals_dict)
					if result is not None:
						print(result)
				except:
					exec(code, globals_dict)
			else:
				exec(code, globals_dict)
				
	except Exception as e:
		print(f"Error: {e}")
	except KeyboardInterrupt:
		print("")
		break
