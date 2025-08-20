import { describe, expect, it } from "vitest";

describe("Basic Tests", () => {
  it("should work with basic math", () => {
    expect(2 + 2).toBe(4);
  });

  it("should handle string operations", () => {
    const str = "Hello World";
    expect(str.toUpperCase()).toBe("HELLO WORLD");
    expect(str.includes("World")).toBe(true);
  });

  it("should work with arrays", () => {
    const arr = [1, 2, 3];
    expect(arr).toHaveLength(3);
    expect(arr.includes(2)).toBe(true);
  });

  it("should work with objects", () => {
    const obj = { name: "Test", value: 42 };
    expect(obj.name).toBe("Test");
    expect(obj).toHaveProperty("value", 42);
  });
});
