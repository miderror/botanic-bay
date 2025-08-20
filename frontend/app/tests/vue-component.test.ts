import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { defineComponent } from "vue";

// Простой тестовый компонент
const TestComponent = defineComponent({
  name: "TestComponent",
  props: {
    message: {
      type: String,
      default: "Hello Vue!",
    },
  },
  template: `
    <div class="test-component">
      <h1>{{ message }}</h1>
      <button @click="count++" data-testid="increment">
        Count: {{ count }}
      </button>
    </div>
  `,
  data() {
    return {
      count: 0,
    };
  },
});

describe("Vue Component Tests", () => {
  it("should render component with default message", () => {
    const wrapper = mount(TestComponent);

    expect(wrapper.find("h1").text()).toBe("Hello Vue!");
    expect(wrapper.find("button").text()).toContain("Count: 0");
  });

  it("should render component with custom message", () => {
    const wrapper = mount(TestComponent, {
      props: {
        message: "Custom Message",
      },
    });

    expect(wrapper.find("h1").text()).toBe("Custom Message");
  });

  it("should increment counter when button is clicked", async () => {
    const wrapper = mount(TestComponent);
    const button = wrapper.find('[data-testid="increment"]');

    expect(button.text()).toContain("Count: 0");

    await button.trigger("click");
    expect(button.text()).toContain("Count: 1");

    await button.trigger("click");
    expect(button.text()).toContain("Count: 2");
  });

  it("should have correct CSS classes", () => {
    const wrapper = mount(TestComponent);

    expect(wrapper.find(".test-component").exists()).toBe(true);
    expect(wrapper.find("h1").exists()).toBe(true);
    expect(wrapper.find("button").exists()).toBe(true);
  });
});
