from gesture_classifier import classify_gesture, count_fingers

test_cases = [
    ([1,1,1,1,1], "Open Hand"),
    ([0,0,0,0,0], "Closed Fist"),
    ([1,0,0,0,0], "Thumbs Up"),
    ([0,1,1,0,0], "Peace / Victory"),
    ([0,1,0,0,1], "Rock"),
    ([0,1,0,0,0], "Pointing"),
    ([1,0,0,0,1], "Call Me"),
]

print("=== Test Gesture Classifier ===")
all_pass = True
for fingers, expected in test_cases:
    result = classify_gesture(fingers)
    jari = count_fingers(fingers)
    status = "PASS" if result["name"] == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    name = result["name"]
    conf = result["confidence"]
    print(f"  {status} | Jari:{fingers} | Expected:{expected} | Got:{name} ({conf:.0%})")

print()
print("Semua test PASS!" if all_pass else "Ada test yang FAIL!")

