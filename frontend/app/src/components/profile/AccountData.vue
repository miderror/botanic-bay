<script setup lang="ts">
/**
 * Компонент для отображения и редактирования персональных данных пользователя
 * Включает имя, телефон, email, скидку и настройки уведомлений
 * Также отображает количество покупок в текущем месяце и прогресс скидки
 */
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ToggleButton from "@/components/common/ToggleButton.vue";
import DeliverySection from "@/components/delivery-section/DeliverySection.vue";
import CartIcon from "@/components/icons/CartIcon.vue";
import ProfileAvatar from "@/components/profile/ProfileAvatar.vue";
import { useEditableField } from "@/composables/useEditableField.ts";
import { useUserStore } from "@/stores/user.ts";
import { storeToRefs } from "pinia";
import { computed, onMounted, ref } from "vue";

const userStore = useUserStore();
const { isLoading, profile, discount, monthlyOrdersAmount, discountPercentageDone } = storeToRefs(userStore);

// TODO: save on server
const phoneNotifications = ref(false);
const emailNotifications = ref(false);

const {
  input: inputName,
  isSaved: isNameSaved,
  showSave: showSaveName,
} = useEditableField(computed(() => profile.value?.full_name));

const phonePattern = /^\+[1-9]\d{6,14}$/;
const {
  input: inputPhone,
  isSaved: isPhoneSaved,
  isValid: isPhoneValid,
  showSave: showSavePhone,
} = useEditableField(
  computed(() => profile.value?.phone_number),
  { validator: (v) => phonePattern.test(v) },
);

const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const {
  input: inputEmail,
  isSaved: isEmailSaved,
  isValid: isEmailValid,
  showSave: showSaveEmail,
} = useEditableField(
  computed(() => profile.value?.email),
  { validator: (v) => emailPattern.test(v) },
);

const saveName = async () => {
  if (!profile.value || !inputName.value) return;
  await userStore.updateName(inputName.value);
};

const savePhone = async () => {
  if (!profile.value || !isPhoneValid.value || !inputPhone.value) return;
  await userStore.updatePhone(inputPhone.value);
};

const saveEmail = async () => {
  if (!profile.value || !isEmailValid.value || !inputEmail.value) return;
  await userStore.updateEmail(inputEmail.value);
};

onMounted(async () => {
  isLoading.value = true;
  await Promise.all([userStore.fetchProfile(), userStore.fetchMonthlyOrders(), userStore.fetchDiscount()]);

  isLoading.value = false;
});
</script>

<template>
  <div class="account-data">
    <h2
      class="section-title"
      style="margin-bottom: 10px"
    >
      Персональная информация
    </h2>
    <LoadingSpinner v-if="isLoading" />

    <!-- Основная информация -->
    <div
      class="data-section"
      v-else
    >
      <div class="action-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>

      <ProfileAvatar />

      <div class="account-info-form">
        <div class="input-wrapper">
          <input
            :class="['account-input', { saved: isNameSaved }]"
            placeholder="Введите имя"
            v-model="inputName"
          />
          <button
            v-if="showSaveName"
            class="save-profile-button"
            @click="saveName"
          >
            OK
          </button>
        </div>

        <div class="input-wrapper">
          <input
            :class="['account-input', { saved: isPhoneSaved }]"
            type="tel"
            v-model="inputPhone"
            placeholder="Введите номер телефона"
          />
          <button
            v-if="showSavePhone"
            class="save-profile-button"
            @click="savePhone"
          >
            OK
          </button>
        </div>

        <div class="input-wrapper">
          <input
            :class="['account-input', { saved: isEmailSaved }]"
            type="tel"
            v-model="inputEmail"
            placeholder="Введите e-mail"
          />
          <button
            v-if="showSaveEmail"
            class="save-profile-button"
            @click="saveEmail"
          >
            OK
          </button>
        </div>
      </div>

      <div class="data-subsection">
        <h3 class="subsection-title">Количество покупок в текущем мес.:</h3>
        <div class="icon-container">
          <CartIcon />
          <span>{{ monthlyOrdersAmount ?? 0 }}</span>
        </div>
      </div>

      <div class="data-subsection">
        <h3 class="subsection-title">Скидка</h3>
        <div class="discount">
          <div :class="['discount__prev', discount?.current_level.toLowerCase()]">
            <span>{{ discount?.current_percent }}%</span>
          </div>
          <div class="discount__data">
            <p>До скидки {{ discount?.next_percent }}% осталось:</p>
            <div class="discount__progress-bar">
              <div :class="['progress', discount?.next_level.toLowerCase()]">
                <div
                  class="progress__fill"
                  :style="{ width: discountPercentageDone + '%' }"
                ></div>
                <span class="progress__text">
                  {{ discount?.current_total }}/{{ discount?.required_total }}
                </span>
              </div>
            </div>
          </div>
          <div :class="['discount__next', discount?.next_level.toLowerCase()]">
            <span>{{ discount?.next_percent }}%</span>
          </div>
        </div>
      </div>

      <div class="data-subsection">
        <h3 class="subsection-title">Уведомления</h3>
        <div class="flex flex-col gap-4">
          <ToggleButton
            text="Телефон"
            v-model="phoneNotifications"
          />
          <ToggleButton
            text="E-mail"
            v-model="emailNotifications"
          />
        </div>
      </div>
    </div>

    <DeliverySection type="saved-addresses" />
  </div>
</template>

<style scoped>
@import "@/assets/styles/profile.css";
</style>
