﻿# 5. Control Flow: If, Else, and Loops

Control flow statements are the building blocks of logic in any programming language. They allow your script to make decisions and perform actions conditionally, or to repeat actions multiple times. In AutoHotkey, this is primarily handled with `If`/`Else` blocks and various types of loops.

## Conditional Execution: The `If` Statement

The `If` statement allows you to execute a block of code only if a certain condition is true. This is the primary way to add decision-making to your scripts.

```autohotkey
UserAge := 25

If (UserAge >= 18)
{
    MsgBox("You are old enough to vote.")
}
```

In this example, the message box will only be shown because the value of `UserAge` (25) is greater than or equal to 18.

### `Else`: Handling the Alternative

You can provide an alternative block of code to execute if the `If` condition is false by using the `Else` statement.

```autohotkey
UserAge := 15

If (UserAge >= 18)
{
    MsgBox("You are old enough to vote.")
}
Else
{
    MsgBox("You are not old enough to vote yet.")
}
```

### Logical Operators

You can create more complex conditions by combining them with logical operators:

-   `&&` or `and`: Logical AND (both conditions must be true)
-   `||` or `or`: Logical OR (at least one condition must be true)
-   `!` or `not`: Logical NOT (inverts the result of a condition)

```autohotkey
IsLoggedIn := true
HasAdminRights := false

; Example of AND
If (IsLoggedIn and HasAdminRights)
{
    MsgBox("Welcome, Administrator!")
}

; Example of OR
If (IsLoggedIn or not HasAdminRights)
{
    MsgBox("User is either logged in or not an admin.")
}
```

## Repeating Actions: Loops

Loops are used to execute a block of code repeatedly. AutoHotkey has several types of loops for different situations.

### The `Loop` Command

The simplest loop repeats a block of code a specific number of times.

```autohotkey
; This loop will run 5 times.
Loop 5
{
    ; A_Index is a built-in variable that contains the number of the current loop iteration.
    MsgBox("This is loop iteration number " A_Index)
}
```

### The `While` Loop

A `While` loop continues to execute as long as a specified condition remains true. This is useful when you don't know in advance how many times you need to loop.

```autohotkey
Counter := 1

While (Counter <= 5)
{
    MsgBox("The counter is now " Counter)
    ; It's crucial to change the variable inside the loop, otherwise it will loop forever!
    Counter := Counter + 1
}
MsgBox("The loop has finished.")
```

### Breaking Out of a Loop

You can exit a loop at any time using the `Break` command. You can also skip the rest of the current iteration and start the next one with the `Continue` command.

```autohotkey
Loop 10
{
    If (A_Index = 3)
        Continue ; Skip the number 3

    If (A_Index = 8)
        Break ; Exit the loop when we reach 8

    MsgBox("The current number is " A_Index)
}
```

## Organizing Code: Functions

As your scripts get larger, you'll want to organize your code into reusable blocks. Functions are perfect for this. A function is a named block of code that performs a specific task and can be "called" from other parts of your script.

### Defining a Function

You define a function with a name, a set of parameters (inputs) in parentheses, and a block of code in curly braces.

```autohotkey
; This function takes two numbers, adds them, and displays the result.
AddTwoNumbers(Num1, Num2)
{
    Sum := Num1 + Num2
    MsgBox("The sum is " Sum)
}
```

### Calling a Function

Once defined, you can execute the function by calling its name and providing values for the parameters.

```autohotkey
; Now we call the function we defined above.
AddTwoNumbers(10, 5)  ; Displays "The sum is 15"
AddTwoNumbers(100, 200) ; Displays "The sum is 300"
```

With the ability to control the flow of your script, you can now create much more intelligent and powerful automations. Next, we'll explore how to give your scripts a face with [GUI Programming](/automation_tools/autohotkey/./06_gui_programming.md).

