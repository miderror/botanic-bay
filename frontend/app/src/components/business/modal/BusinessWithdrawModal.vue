<script setup lang="ts">
import BaseModal from "@/components/common/BaseModal.vue";
import NotificationToast from "@/components/common/NotificationToast.vue";
import { useNotification } from "@/composables/useNotification.ts";
import { useBusinessStore } from "@/stores/business.ts";
import { logger } from "@/utils/logger.ts";
import { storeToRefs } from "pinia";
import { computed, ref } from "vue";

const store = useBusinessStore();
const { isWithdrawModalOpen, balance } = storeToRefs(store);

const { message, type, show, showNotification } = useNotification();

const bankCode = ref<string>("");
const accountNumber = ref<string>("");
const withdrawAmount = ref<number | null>(null);

// простые валидаторы
const isBankCodeValid = computed(() => /^[A-Za-z0-9]{8,11}$/.test(bankCode.value));
const isIbanValid = computed(() => /^[A-Za-z0-9]{5,34}$/.test(accountNumber.value));
const isAmountValid = computed(
  () =>
    typeof withdrawAmount.value === "number" &&
    withdrawAmount.value >= 1 &&
    withdrawAmount.value <= (balance.value ?? 0),
);

// итоговый флаг формы
const isFormValid = computed(() => isBankCodeValid.value && isIbanValid.value && isAmountValid.value);

const onButtonClick = async () => {
  if (!isFormValid.value || !withdrawAmount.value) return;
  try {
    await store.onSendWithdrawRequest({
      bank_code: bankCode.value,
      account_number: accountNumber.value,
      amount: withdrawAmount.value,
    });
    showNotification("Заявка на вывод отправлена", "success");
    await store.fetchProfile();
  } catch (e) {
    logger.error("Error while withdrawing money", e);
    showNotification("Произошла ошибка при выводе средств", "error");
  }
};
</script>

<template>
  <BaseModal
    :modelValue="isWithdrawModalOpen"
    @close="store.isWithdrawModalOpen = false"
    @update:modelValue="store.isWithdrawModalOpen = $event"
    minimized
    :overlayBg="true"
    :closeOnOverlayClick="true"
  >
    <div class="business-modal_withdraw-content">
      <h2 class="business-modal_withdraw-name">Вывести</h2>

      <div class="business-modal_withdraw-info-container">
        <div class="business-modal_withdraw-input-grid">
          <!-- BIC/SWIFT -->
          <div class="input-group">
            <input
              v-model="bankCode"
              :class="['modal-input', { 'error-border': bankCode && !isBankCodeValid }]"
              placeholder="БИК банка - получателя или SWIFT - код"
              type="text"
              maxlength="11"
            />
            <p
              v-if="bankCode && !isBankCodeValid"
              class="input-error"
            >
              Неверный формат (8–11 букв/цифр).
            </p>
          </div>

          <!-- IBAN -->
          <div class="input-group">
            <input
              v-model="accountNumber"
              :class="['modal-input', { 'error-border': accountNumber && !isIbanValid }]"
              placeholder="Счет получателя или IBAN"
              type="text"
              maxlength="34"
            />
            <p
              v-if="accountNumber && !isIbanValid"
              class="input-error"
            >
              Неверный формат (5–34 букв/цифр).
            </p>
          </div>

          <!-- Сумма -->
          <div class="input-group">
            <input
              v-model.number="withdrawAmount"
              :class="['modal-input', { 'error-border': withdrawAmount !== null && !isAmountValid }]"
              type="number"
              placeholder="Введите сумму"
              :min="1"
              :max="balance"
            />
            <p
              v-if="withdrawAmount !== null && !isAmountValid"
              class="input-error"
            >
              Сумма от 1 до {{ balance }}.
            </p>
          </div>
        </div>
      </div>

      <div class="business-modal_withdraw-button-container">
        <button
          class="modal-button"
          :disabled="!isFormValid"
          @click="onButtonClick"
        >
          Перевести
        </button>
      </div>
    </div>

    <NotificationToast
      :show="show"
      :message="message"
      :type="type"
    />
  </BaseModal>
</template>

<style scoped>
@import "@/assets/styles/modal.css";
@import "@/assets/styles/business-withdraw-modal.css";

.input-group {
  position: relative;
}

/* подсказка ошибки */
.input-error {
  margin: 4px 0 0 4px;
  color: #e74c3c;
  font-size: 12px;
}

/* если поле с классом error, добавляем рамку */
.modal-input.error {
  border: 1px solid #e74c3c;
}
</style>
