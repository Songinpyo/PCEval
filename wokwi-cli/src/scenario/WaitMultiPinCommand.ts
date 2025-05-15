import chalkTemplate from 'chalk-template';
import type { APIClient } from '../APIClient.js';
import type { IScenarioCommand, TestScenario } from '../TestScenario.js';

interface PinCondition {
  'part-id': string;
  pin: string;
  value: number;
}

export interface IWaitMultiPinParams {
  pins: PinCondition[];
  timeout?: number; // milliseconds, default: 5000
  interval?: number; // milliseconds, default: 100
}

const DEFAULT_TIMEOUT = 5000;
const DEFAULT_INTERVAL = 100;

export class WaitMultiPinCommand implements IScenarioCommand {
  async run(scenario: TestScenario, client: APIClient, params: IWaitMultiPinParams): Promise<void> {
    const { pins, timeout = DEFAULT_TIMEOUT, interval = DEFAULT_INTERVAL } = params;
    const startTime = Date.now();

    if (!pins || pins.length === 0) {
      scenario.fail('WaitMultiPin Error: No pins specified.');
      return Promise.reject(new Error('No pins specified for wait-multi-pin'));
    }

    const pinDescriptions = pins
      .map((p) => chalkTemplate`{yellow ${p['part-id']}}:{magenta ${p.pin}} == {yellow ${p.value}}`)
      .join(', ');
    scenario.log(chalkTemplate`wait-multi-pin ${pinDescriptions} (timeout: ${timeout}ms)`);

    return new Promise((resolve, reject) => {
      let intervalId: NodeJS.Timeout | null = null;
      let timeoutId: NodeJS.Timeout | null = null;

      const cleanup = () => {
        if (intervalId) clearInterval(intervalId);
        if (timeoutId) clearTimeout(timeoutId);
      };

      const checkPins = async () => {
        try {
          const readPromises = pins.map((pin) => client.pinRead(pin['part-id'], pin.pin));
          const pinInfos = await Promise.all(readPromises);
          const currentValues = pinInfos.map((info) => (info?.value ? 1 : 0));

          let allMatched = true;
          const mismatches: string[] = [];
          for (let i = 0; i < pins.length; i++) {
            if (currentValues[i] !== pins[i].value) {
              allMatched = false;
              mismatches.push(
                chalkTemplate`{yellow ${pins[i]['part-id']}}:{magenta ${pins[i].pin}} expected {yellow ${pins[i].value}} but was {red ${currentValues[i]}}`,
              );
            }
          }

          if (allMatched) {
            scenario.log(chalkTemplate`WaitMultiPin Success: All pins matched. ${pinDescriptions}`);
            cleanup();
            resolve();
          } else if (Date.now() - startTime > timeout) {
            const errorMessage = chalkTemplate`WaitMultiPin Timeout: Not all pins matched within ${timeout}ms. Mismatches: ${mismatches.join(', ')}`;
            scenario.fail(errorMessage);
            cleanup();
            reject(new Error('WaitMultiPin Timeout'));
          }
        } catch (error) {
          const errorMessage = chalkTemplate`WaitMultiPin Error reading pins: ${(error as Error).message}`;
          scenario.fail(errorMessage);
          cleanup();
          reject(error);
        }
      };

      intervalId = setInterval(() => void checkPins(), interval);

      timeoutId = setTimeout(() => {
        cleanup();
        void checkPins().catch(() => {
             const errorMessage = chalkTemplate`WaitMultiPin Timeout: Not all pins matched within ${timeout}ms.`;
             scenario.fail(errorMessage);
             reject(new Error('WaitMultiPin Timeout'));
        });
      }, timeout + interval);
      void checkPins();
    });
  }
} 